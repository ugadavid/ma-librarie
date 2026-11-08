import os
import sqlite3
import stat
import time
import zipfile
import zlib
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from .windows import SourceProblem, is_reparse, locate, verify


SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS roots (
    id INTEGER PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id),
    path TEXT NOT NULL,
    volume TEXT NOT NULL,
    relative TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'new',
    revision INTEGER NOT NULL DEFAULT 0,
    UNIQUE (collection_id, volume, relative)
);
CREATE TABLE IF NOT EXISTS entries (
    root_id INTEGER NOT NULL REFERENCES roots(id),
    relative TEXT NOT NULL,
    parent TEXT NOT NULL,
    name TEXT NOT NULL,
    volume_path TEXT NOT NULL,
    kind TEXT NOT NULL,
    extension TEXT NOT NULL,
    size INTEGER NOT NULL,
    modified INTEGER NOT NULL,
    first_seen INTEGER NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    state TEXT NOT NULL,
    PRIMARY KEY (root_id, relative, kind)
);
CREATE INDEX IF NOT EXISTS entries_volume_path ON entries (volume_path);
CREATE INDEX IF NOT EXISTS entries_parent ON entries (root_id, parent, kind);
"""
SORTS = {
    "Nom": "fold(name), name",
    "Taille": "size DESC",
    "Modification": "modified DESC",
    "Première détection": "detected DESC",
}
PACKAGE_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
DC = "{http://purl.org/dc/elements/1.1/}"


@dataclass(frozen=True)
class Entry:
    name: str
    kind: str
    extension: str
    size: int
    modified: int
    title: str = ""
    author: str = ""


@dataclass
class Scan:
    entries: dict = field(default_factory=dict)
    blocked: set = field(default_factory=set)
    errors: list = field(default_factory=list)

    def fail(self, relative, error):
        self.blocked.add(relative)
        self.errors.append(f"{relative or '.'} — {error}")

    def is_blocked(self, relative):
        while relative and relative not in self.blocked:
            relative = os.path.dirname(relative)
        return relative in self.blocked


@dataclass
class Summary:
    added: set = field(default_factory=set)
    changed: set = field(default_factory=set)
    missing: set = field(default_factory=set)
    errors: list = field(default_factory=list)


def epub_metadata(path):
    with zipfile.ZipFile(path) as book:
        def read_xml(name):
            with book.open(name) as stream:
                data = stream.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("Métadonnées EPUB trop volumineuses")
            return ElementTree.fromstring(data)

        container = read_xml("META-INF/container.xml")
        package = container.find(f".//{{{PACKAGE_NS}}}rootfile")
        if package is None:
            raise ValueError("Paquet EPUB introuvable")
        opf = read_xml(package.attrib["full-path"])
        return tuple(
            " / ".join("".join(node.itertext()).strip()
                       for node in opf.iter(f"{DC}{tag}") if "".join(node.itertext()).strip())
            for tag in ("title", "creator")
        )


def inventory(source, previous):
    result = Scan()
    pending = [""]
    while pending:
        relative = pending.pop()
        folder = source.scan_path / relative
        try:
            info = folder.lstat()
            if is_reparse(info):
                result.blocked.add(relative)
                continue
            with os.scandir(folder) as children:
                for child in children:
                    key = os.path.join(relative, child.name)
                    try:
                        info = child.stat(follow_symlinks=False)
                    except OSError as exc:
                        result.fail(key, exc)
                        continue
                    if is_reparse(info):
                        result.blocked.add(key)
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(key)
                        result.entries[key] = Entry(child.name, "dir", "", 0, 0)
                    elif stat.S_ISREG(info.st_mode):
                        extension = Path(child.name).suffix.removeprefix(".").casefold()
                        metadata = ("", "")
                        if extension == "epub":
                            old = previous.get((key, "file"))
                            if (old and old["size"] == info.st_size
                                    and old["modified"] == info.st_mtime_ns
                                    and (old["title"] or old["author"])):
                                metadata = old["title"], old["author"]
                            else:
                                try:
                                    metadata = epub_metadata(child.path)
                                except (OSError, ValueError, KeyError, RuntimeError,
                                        NotImplementedError, ElementTree.ParseError,
                                        zipfile.BadZipFile, EOFError, zlib.error) as exc:
                                    result.errors.append(f"{key} — Métadonnées EPUB : {exc}")
                        result.entries[key] = Entry(
                            child.name, "file", extension, info.st_size, info.st_mtime_ns, *metadata
                        )
        except OSError as exc:
            result.fail(relative, exc)
    return result


class Catalogue:
    def __init__(self, filename):
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.filename)
        db.row_factory = sqlite3.Row
        db.create_function("fold", 1, str.casefold, deterministic=True)
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def collections(self):
        with self.connect() as db:
            return db.execute("SELECT * FROM collections ORDER BY fold(name), id").fetchall()

    def create_collection(self, name):
        if not name.strip():
            raise ValueError("Donnez un nom à la collection.")
        with self.connect() as db:
            return db.execute(
                "INSERT INTO collections (name) VALUES (?)", (name.strip(),)
            ).lastrowid

    def roots(self, collection):
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM roots WHERE collection_id = ? ORDER BY id", (collection,)
            ).fetchall()

    def add_root(self, collection, folder):
        source = locate(folder)
        data = locate(self.filename.parent)
        if source.volume == data.volume and Path(data.relative).is_relative_to(source.relative):
            raise ValueError("Ce dossier contient les données de l’application. Choisissez un sous-dossier.")
        with self.connect() as db:
            return db.execute(
                "INSERT INTO roots (collection_id, path, volume, relative) VALUES (?, ?, ?, ?)",
                (collection, str(source.path), source.volume, source.relative),
            ).lastrowid

    def relocate(self, root, folder):
        source = verify(folder, root["volume"], root["relative"])
        with self.connect() as db:
            updated = db.execute(
                """UPDATE roots SET path = ?, state = 'new', revision = revision + 1
                   WHERE id = ? AND revision = ?""",
                (str(source.path), root["id"], root["revision"]),
            )
            if not updated.rowcount:
                raise ValueError("La source a changé dans une autre instance. Actualisez la vue.")

    def directories(self, root_id, parent):
        with self.connect() as db:
            return db.execute(
                """SELECT relative, name, state FROM entries
                   WHERE root_id = ? AND parent = ? AND kind = 'dir' AND state != 'missing'
                   ORDER BY fold(name), name""",
                (root_id, parent),
            ).fetchall()

    def extensions(self, collection):
        with self.connect() as db:
            return [row[0] for row in db.execute(
                """SELECT DISTINCT extension FROM entries JOIN roots ON roots.id = root_id
                   WHERE collection_id = ? AND kind = 'file' ORDER BY extension""",
                (collection,),
            )]

    def search(self, collection, query="", extension=None, sort="Nom", scope=None,
               limit=200, offset=0):
        terms = query.casefold().split()
        filters = [
            r"instr(fold(name || char(10) || full_path || char(10) || title || char(10) || author), ?) > 0"
            for _ in terms
        ]
        args = [collection, *terms]
        if extension is not None:
            filters.append("extension = ?")
            args.append(extension)
        if scope:
            root_id, directory = scope
            filters.append("root_id = ?")
            args.append(root_id)
            if directory:
                prefix = directory + os.sep
                filters.append("substr(relative, 1, length(?)) = ?")
                args.extend((prefix, prefix))
        where = " AND ".join(filters) or "1"
        order = SORTS[sort]
        with self.connect() as db:
            return db.execute(
                f"""
                WITH files AS (
                    SELECT entries.*, roots.volume, roots.relative AS root_relative,
                           roots.path AS root_path, roots.state AS root_state,
                           rtrim(roots.path, ?) || ? || entries.relative AS full_path,
                           MIN(first_seen) OVER (PARTITION BY volume, volume_path) AS detected
                    FROM entries JOIN roots ON roots.id = root_id
                    WHERE collection_id = ? AND kind = 'file'
                ), ranked AS (
                    SELECT *, ROW_NUMBER() OVER (
                        PARTITION BY volume, volume_path
                        ORDER BY CASE
                            WHEN root_state IN ('available', 'partial') AND state = 'available' THEN 0
                            WHEN root_state IN ('available', 'partial') AND state = 'missing' THEN 2
                            ELSE 1 END, root_id
                    ) AS preference
                    FROM files WHERE {where}
                )
                SELECT * FROM ranked WHERE preference = 1
                ORDER BY {order}, volume, volume_path LIMIT ? OFFSET ?
                """,
                (os.sep, os.sep, *args, limit, offset),
            ).fetchall()

    def synchronize(self, collection, progress=lambda message: None):
        summary = Summary()
        now = time.time_ns()
        for root in self.roots(collection):
            progress(root["path"])
            with self.connect() as db:
                previous = {(row["relative"], row["kind"]): row for row in db.execute(
                    "SELECT * FROM entries WHERE root_id = ?", (root["id"],)
                )}
            try:
                source = verify(root["path"], root["volume"], root["relative"])
                scan = inventory(source, previous)
                verify(root["path"], root["volume"], root["relative"])
                state = "error" if "" in scan.blocked else "partial" if scan.errors else "available"
                errors = scan.errors
            except SourceProblem as exc:
                scan = None
                state = exc.state
                errors = [str(exc)]

            with self.connect() as db:
                updated = db.execute(
                    """UPDATE roots SET state = ?, revision = revision + 1
                       WHERE id = ? AND revision = ?""",
                    (state, root["id"], root["revision"]),
                )
                if not updated.rowcount:
                    summary.errors.append(f"{root['path']} — Source modifiée. Relancez la synchronisation.")
                    continue
                if scan is not None and state != "error":
                    self.apply_scan(db, root, scan, previous, now, summary)
            summary.errors.extend(f"{root['path']} — {error}" for error in errors)
        with self.connect() as db:
            for volume, key in list(summary.missing):
                if db.execute(
                    """SELECT 1 FROM entries JOIN roots ON roots.id = root_id
                       WHERE collection_id = ? AND volume = ? AND volume_path = ?
                             AND kind = 'file' AND entries.state = 'available'
                             AND roots.state IN ('available', 'partial') LIMIT 1""",
                    (collection, volume, key),
                ).fetchone():
                    summary.missing.discard((volume, key))
        summary.changed.difference_update(summary.added)
        return summary

    @staticmethod
    def apply_scan(db, root, scan, previous, now, summary):
        rows = []
        applied = set()
        for relative, entry in scan.entries.items():
            identity = relative, entry.kind
            old = previous.get(identity)
            if scan.is_blocked(relative) and (old or entry.kind == "file"):
                continue
            applied.add(identity)
            first = old["first_seen"] if old else now
            key = os.path.normpath(os.path.join(root["relative"], relative))
            fields = (entry.kind, entry.extension, entry.size, entry.modified, entry.title, entry.author)
            state = "error" if scan.is_blocked(relative) else "available"
            rows.append((root["id"], relative, os.path.dirname(relative), entry.name,
                         key, *fields[:4], first, *fields[4:], state))
            if entry.kind == "file":
                if not old:
                    known = db.execute(
                        """SELECT 1 FROM entries JOIN roots ON roots.id = root_id
                           WHERE collection_id = ? AND volume = ? AND volume_path = ?
                                 AND kind = 'file' LIMIT 1""",
                        (root["collection_id"], root["volume"], key),
                    ).fetchone()
                    if not known:
                        summary.added.add((root["volume"], key))
                elif old["state"] == "missing" or fields != tuple(old[column] for column in (
                        "kind", "extension", "size", "modified", "title", "author")):
                    summary.changed.add((root["volume"], key))

        db.executemany("INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        updates = []
        for (relative, kind), old in previous.items():
            if (relative, kind) in applied:
                continue
            state = "error" if scan.is_blocked(relative) else "missing"
            if state == "missing" and old["state"] != "missing" and kind == "file":
                summary.missing.add((root["volume"], old["volume_path"]))
            if old["state"] != state:
                updates.append((state, root["id"], relative, kind))
        db.executemany("UPDATE entries SET state = ? WHERE root_id = ? AND relative = ? AND kind = ?", updates)
