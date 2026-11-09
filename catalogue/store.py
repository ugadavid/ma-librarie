import json
import os
import sqlite3
import stat
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from .book_metadata import BOOK_EXTENSIONS, EMPTY, MetadataError, book_metadata, companion_metadata
from .windows import SourceProblem, is_reparse, locate, verify


SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS collection_libraries (
    collection_id INTEGER PRIMARY KEY REFERENCES collections(id) ON DELETE CASCADE,
    library TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS collection_libraries_by_library
    ON collection_libraries (library, collection_id);
CREATE TABLE IF NOT EXISTS library_extension_filters (
    library TEXT PRIMARY KEY, extensions TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS extension_filters (
    collection_id INTEGER PRIMARY KEY REFERENCES collections(id) ON DELETE CASCADE,
    extensions TEXT NOT NULL
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
    title_source TEXT NOT NULL DEFAULT '',
    author_source TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (root_id, relative, kind)
);
CREATE TABLE IF NOT EXISTS column_widths (
    column_name TEXT PRIMARY KEY, width INTEGER NOT NULL CHECK (width > 0)
);
CREATE TABLE IF NOT EXISTS catalogue_ids (
    kind TEXT PRIMARY KEY, last_id INTEGER NOT NULL
);
INSERT OR IGNORE INTO catalogue_ids SELECT 'collections', COALESCE(MAX(id), 0) FROM collections;
INSERT OR IGNORE INTO catalogue_ids SELECT 'roots', COALESCE(MAX(id), 0) FROM roots;
CREATE INDEX IF NOT EXISTS entries_volume_path ON entries (volume_path);
CREATE INDEX IF NOT EXISTS entries_parent ON entries (root_id, parent, kind);
"""
UNCLASSIFIED = "unclassified"
LIBRARIES = {
    "books": ("Livres", "Tous les livres"),
    "movies": ("Films", "Tous les films"),
    "music": ("Musiques", "Toutes les musiques"),
    UNCLASSIFIED: ("À classer", "Toutes les collections à classer"),
}
STATES = {
    "new": "À synchroniser",
    "available": "Disponible",
    "partial": "Inventaire partiel",
    "offline": "Hors ligne",
    "relocate": "À relocaliser",
    "error": "Accès impossible",
    "missing": "Absent",
}
SORTS = {
    "Nom": "fold(name)",
    "Collections": "fold(collection_names)",
    "Extension": "fold(extension)",
    "Taille": "size",
    "Modification": "modified",
    "Première détection": "detected",
    "État": "state_order(CASE WHEN root_state IN ('available', 'partial') THEN state ELSE root_state END)",
}
DEFAULT_DESCENDING = {"Taille", "Modification", "Première détection"}


@dataclass(frozen=True)
class Entry:
    name: str
    kind: str
    extension: str
    size: int
    modified: int
    title: str = ""
    author: str = ""
    title_source: str = ""
    author_source: str = ""


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


def inventory(source, previous, on_examined=None):
    result = Scan()
    pending = [""]
    examined = 0
    last_report = 0
    while pending:
        relative = pending.pop()
        folder = source.scan_path / relative
        try:
            info = folder.lstat()
            if is_reparse(info):
                result.blocked.add(relative)
                continue
            files = []
            companion_unknown = False
            with os.scandir(folder) as children:
                for child in children:
                    key = os.path.join(relative, child.name)
                    is_companion = child.name.casefold() == "metadata.opf"
                    try:
                        info = child.stat(follow_symlinks=False)
                    except OSError as exc:
                        result.fail(key, exc)
                        companion_unknown |= is_companion
                        continue
                    if is_reparse(info):
                        result.blocked.add(key)
                        companion_unknown |= is_companion
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        pending.append(key)
                        result.entries[key] = Entry(child.name, "dir", "", 0, 0)
                    elif stat.S_ISREG(info.st_mode):
                        extension = Path(child.name).suffix.removeprefix(".").casefold()
                        files.append((child, key, info, extension))

            books = [child.name for child, _, _, extension in files if extension in BOOK_EXTENSIONS]
            sidecars = [child for child, _, _, _ in files if child.name.casefold() == "metadata.opf"]
            companion, matched = EMPTY, set()
            if companion_unknown:
                companion = None
            elif books and len(sidecars) == 1:
                try:
                    companion, matched = companion_metadata(Path(sidecars[0].path), books)
                except (OSError, MetadataError) as exc:
                    result.errors.append(f"{os.path.join(relative, sidecars[0].name)} — {exc}")
                    companion = None

            for child, key, info, extension in files:
                metadata = ()
                if extension in BOOK_EXTENSIONS:
                    fields = companion if companion is None or child.name in matched else EMPTY
                    metadata = book_metadata(
                        Path(child.path), extension, info.st_size, info.st_mtime_ns,
                        previous.get((key, "file")), fields, result.errors, key,
                    )
                result.entries[key] = Entry(
                    child.name, "file", extension, info.st_size, info.st_mtime_ns, *metadata
                )
                examined += 1
                if on_examined is not None:
                    now = time.monotonic()
                    if now - last_report >= 0.15:
                        on_examined(examined)
                        last_report = now
        except OSError as exc:
            result.fail(relative, exc)
    if on_examined is not None:
        on_examined(examined)
    return result


@dataclass(frozen=True)
class ScanProgress:
    path: str
    position: int
    total: int
    examined: int = 0


class Catalogue:
    def __init__(self, filename):
        self.filename = Path(filename)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript(SCHEMA)
            db.execute("BEGIN IMMEDIATE")
            columns = {row["name"] for row in db.execute("PRAGMA table_info(entries)")}
            for field in ("title", "author"):
                if f"{field}_source" not in columns:
                    db.execute(f"ALTER TABLE entries ADD COLUMN {field}_source TEXT NOT NULL DEFAULT ''")
                    db.execute(
                        f"""UPDATE entries SET {field}_source = 'epub-embedded'
                            WHERE extension = 'epub' AND {field} != ''"""
                    )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.filename)
        db.row_factory = sqlite3.Row
        db.create_function("fold", 1, str.casefold, deterministic=True)
        db.create_function("state_order", 1, lambda state: STATES[state].casefold(),
                           deterministic=True)
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def mutation(self):
        # One writer or scanner at a time, including other app instances.
        # The lock is local to the catalogue and is released when the handle closes.
        import msvcrt

        lock_path = self.filename.with_suffix(self.filename.suffix + ".lock")
        with lock_path.open("a+b") as lock:
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise OSError("Catalogue occupé. Attendez la fin de l’opération en cours ou réessayez.") from exc
            try:
                yield
            finally:
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

    @staticmethod
    def collection_name(name):
        name = name.strip()
        if not name:
            raise ValueError("Donnez un nom à la collection.")
        return name

    @staticmethod
    def next_id(db, kind):
        # An ID held by another window must never refer to a replacement item.
        return db.execute(
            "UPDATE catalogue_ids SET last_id = last_id + 1 WHERE kind = ? RETURNING last_id",
            (kind,),
        ).fetchone()[0]

    def column_widths(self):
        with self.connect() as db:
            return dict(db.execute("SELECT column_name, width FROM column_widths"))

    def save_column_widths(self, widths):
        with self.connect() as db:
            db.executemany(
                """INSERT INTO column_widths (column_name, width) VALUES (?, ?)
                   ON CONFLICT (column_name) DO UPDATE SET width = excluded.width""",
                widths.items(),
            )

    def collections(self, library=None):
        where, args = self.collection_scope(None, library) if library is not None else ("1", ())
        with self.connect() as db:
            return db.execute(
                f"""SELECT collections.*, COALESCE(library, ?) AS library
                    FROM collections LEFT JOIN collection_libraries ON collection_id = collections.id
                    WHERE {where} ORDER BY fold(name), id""",
                (UNCLASSIFIED, *args),
            ).fetchall()

    def create_collection(self, name, library=UNCLASSIFIED):
        name = self.collection_name(name)
        with self.mutation(), self.connect() as db:
            collection = self.next_id(db, "collections")
            db.execute("INSERT INTO collections (id, name) VALUES (?, ?)", (collection, name))
            self.assign_library(db, collection, library)
            return collection

    def move_collection(self, collection, library):
        with self.mutation(), self.connect() as db:
            if not db.execute("SELECT 1 FROM collections WHERE id = ?", (collection,)).fetchone():
                raise ValueError("Cette collection n’existe plus.")
            self.assign_library(db, collection, library)

    @staticmethod
    def assign_library(db, collection, library):
        if library not in LIBRARIES:
            raise ValueError("Bibliothèque inconnue.")
        if library == UNCLASSIFIED:
            db.execute("DELETE FROM collection_libraries WHERE collection_id = ?", (collection,))
        else:
            db.execute(
                """INSERT INTO collection_libraries (collection_id, library) VALUES (?, ?)
                   ON CONFLICT (collection_id) DO UPDATE SET library = excluded.library""",
                (collection, library),
            )

    def rename_collection(self, collection, name):
        name = self.collection_name(name)
        with self.mutation(), self.connect() as db:
            updated = db.execute("UPDATE collections SET name = ? WHERE id = ?", (name, collection))
            if not updated.rowcount:
                raise ValueError("Cette collection n’existe plus.")

    def delete_collection(self, collection):
        with self.mutation(), self.connect() as db:
            db.execute("DELETE FROM entries WHERE root_id IN (SELECT id FROM roots WHERE collection_id = ?)",
                       (collection,))
            db.execute("DELETE FROM roots WHERE collection_id = ?", (collection,))
            deleted = db.execute("DELETE FROM collections WHERE id = ?", (collection,))
            if not deleted.rowcount:
                raise ValueError("Cette collection n’existe plus.")

    def remove_root(self, collection, root_id):
        with self.mutation(), self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            roots = db.execute(
                "SELECT * FROM roots WHERE collection_id = ?", (collection,)
            ).fetchall()
            removed = next((root for root in roots if root["id"] == root_id), None)
            if removed is None:
                raise ValueError("Cette racine n’existe plus.")
            removed_parts = Path(removed["relative"]).parts
            for other in roots:
                if other["id"] == root_id or other["volume"] != removed["volume"]:
                    continue
                parts = Path(other["relative"]).parts
                shared = min(len(parts), len(removed_parts))
                if parts[:shared] == removed_parts[:shared]:
                    self.preserve_covered_entries(db, removed, other, parts)
            db.execute("DELETE FROM entries WHERE root_id = ?", (root_id,))
            db.execute("DELETE FROM roots WHERE id = ?", (root_id,))

    @staticmethod
    def preserve_covered_entries(db, removed, other, root_parts):
        entries = db.execute("SELECT * FROM entries WHERE root_id = ?", (removed["id"],))
        ancestors = {}
        for entry in entries:
            parts = Path(entry["volume_path"]).parts
            depth = len(root_parts)
            if parts[:depth] != root_parts or len(parts) <= depth:
                continue
            relative = os.path.join(*parts[depth:])
            parent = os.path.dirname(relative)
            state = entry["state"]
            if state == "available" and removed["state"] not in ("available", "partial"):
                state = "error"
            db.execute(
                """INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (root_id, relative, kind) DO UPDATE SET
                       first_seen = min(entries.first_seen, excluded.first_seen)""",
                (other["id"], relative, parent, entry["name"], entry["volume_path"], entry["kind"],
                 entry["extension"], entry["size"], entry["modified"], entry["first_seen"],
                 entry["title"], entry["author"], state, entry["title_source"], entry["author_source"]),
            )
            if state != "missing":
                # A nested source has no entry for its own root directory.
                while parent and parent not in ancestors:
                    ancestors[parent] = entry["first_seen"]
                    parent = os.path.dirname(parent)

        db.executemany(
            """INSERT OR IGNORE INTO entries VALUES (?, ?, ?, ?, ?, 'dir', '', 0, 0, ?, '', '', 'error', '', '')""",
            ((other["id"], parent, os.path.dirname(parent), os.path.basename(parent),
              os.path.normpath(os.path.join(other["relative"], parent)), first_seen)
             for parent, first_seen in ancestors.items()),
        )

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
        with self.mutation(), self.connect() as db:
            root_id = self.next_id(db, "roots")
            db.execute(
                "INSERT INTO roots (id, collection_id, path, volume, relative) VALUES (?, ?, ?, ?, ?)",
                (root_id, collection, str(source.path), source.volume, source.relative),
            )
            return root_id

    def relocate(self, root, folder):
        source = verify(folder, root["volume"], root["relative"])
        with self.mutation(), self.connect() as db:
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

    @staticmethod
    def collection_scope(collection, library):
        if library is None:
            return "collections.id = ?", (collection,)
        if library == UNCLASSIFIED:
            return "collection_libraries.collection_id IS NULL", ()
        return "collection_libraries.library = ?", (library,)

    def extensions(self, collection, *, library=None):
        where, args = self.collection_scope(collection, library)
        with self.connect() as db:
            return [row[0] for row in db.execute(
                f"""SELECT DISTINCT extension FROM entries JOIN roots ON roots.id = root_id
                    JOIN collections ON collections.id = roots.collection_id
                    LEFT JOIN collection_libraries ON collection_libraries.collection_id = collections.id
                    WHERE {where} AND kind = 'file' ORDER BY extension""",
                args,
            )]

    @staticmethod
    def filter_target(collection, library):
        if library is None:
            return "extension_filters", "collection_id", collection
        return "library_extension_filters", "library", library

    def extension_filter(self, collection, *, library=None):
        """None matches every format, while an empty set matches no files."""
        table, key, value = self.filter_target(collection, library)
        with self.connect() as db:
            row = db.execute(
                f"SELECT extensions FROM {table} WHERE {key} = ?", (value,)
            ).fetchone()
            return frozenset(json.loads(row["extensions"])) if row else None

    def set_extension_filter(self, collection, extensions, *, library=None):
        table, key, value = self.filter_target(collection, library)
        with self.connect() as db:
            if extensions is None:
                db.execute(f"DELETE FROM {table} WHERE {key} = ?", (value,))
            else:
                db.execute(
                    f"""INSERT INTO {table} ({key}, extensions) VALUES (?, ?)
                        ON CONFLICT ({key}) DO UPDATE SET extensions = excluded.extensions""",
                    (value, json.dumps(sorted(set(extensions)))),
                )

    @staticmethod
    def file_filters(extension, scope, relative_column="relative"):
        filters = []
        args = []
        if extension is not None:
            selected = (extension,) if isinstance(extension, str) else tuple(extension)
            if not selected:
                return ["0"], []
            placeholders = ", ".join("?" for _ in selected)
            filters.append(f"extension IN ({placeholders})")
            args.extend(selected)
        if scope:
            root_id, directory = scope
            filters.append("root_id = ?")
            args.append(root_id)
            if directory:
                prefix = directory + os.sep
                filters.append(f"substr({relative_column}, 1, length(?)) = ?")
                args.extend((prefix, prefix))
        return filters, args

    def duplicate_candidates(self, collection, extension, scope, library):
        collections_where, collections_args = self.collection_scope(collection, library)
        filters, args = self.file_filters(extension, scope, "entries.relative")
        where = " AND ".join([collections_where, "kind = 'file'", *filters])
        with self.connect() as db:
            return db.execute(
                f"""SELECT entries.name, entries.relative, volume_path, roots.volume,
                           roots.relative AS root_relative, roots.path AS root_path,
                           collections.name AS collection_name,
                           rtrim(roots.path, ?) || ? || entries.relative AS full_path
                    FROM entries JOIN roots ON roots.id = root_id
                    JOIN collections ON collections.id = roots.collection_id
                    LEFT JOIN collection_libraries ON collection_libraries.collection_id = collections.id
                    WHERE {where}
                    ORDER BY CASE WHEN roots.state IN ('available', 'partial')
                                      AND entries.state = 'available' THEN 0 ELSE 1 END, root_id""",
                (os.sep, os.sep, *collections_args, *args),
            ).fetchall()

    def search(self, collection, query="", extension=None, sort="Nom", scope=None,
               limit=200, offset=0, *, descending=None, library=None):
        terms = query.casefold().split()
        filters = [
            r"instr(fold(name || char(10) || full_path || char(10) || title || char(10) || author), ?) > 0"
            for _ in terms
        ]
        scope_filters, scope_args = self.file_filters(extension, scope)
        filters.extend(scope_filters)
        args = [*terms, *scope_args]
        where = " AND ".join(filters) or "1"
        collections_where, collections_args = self.collection_scope(collection, library)
        order = SORTS[sort]
        if descending is None:
            descending = sort in DEFAULT_DESCENDING
        direction = "DESC" if descending else "ASC"
        membership = "collection_name"
        if library is not None:
            # Use all indexed aliases in the active library, even if only one matched the query.
            membership = """
                (SELECT group_concat(name, ' · ') FROM (
                    SELECT DISTINCT eligible.name FROM entries AS aliases
                    JOIN roots ON roots.id = aliases.root_id
                    JOIN eligible ON eligible.id = roots.collection_id
                    WHERE aliases.volume_path = ranked.volume_path AND roots.volume = ranked.volume
                          AND aliases.kind = 'file'
                    ORDER BY fold(eligible.name), eligible.name
                ))
            """
        with self.connect() as db:
            return db.execute(
                f"""
                WITH eligible AS (
                    SELECT collections.id, collections.name FROM collections
                    LEFT JOIN collection_libraries ON collection_id = collections.id
                    WHERE {collections_where}
                ), files AS (
                    SELECT entries.*, roots.volume, roots.relative AS root_relative,
                           roots.path AS root_path, roots.state AS root_state,
                           eligible.name AS collection_name,
                           rtrim(roots.path, ?) || ? || entries.relative AS full_path,
                           MIN(first_seen) OVER (PARTITION BY volume, volume_path) AS detected
                    FROM entries JOIN roots ON roots.id = root_id
                    JOIN eligible ON eligible.id = roots.collection_id
                    WHERE kind = 'file'
                ), ranked AS (
                    SELECT *, ROW_NUMBER() OVER (
                        PARTITION BY volume, volume_path
                        ORDER BY CASE
                            WHEN root_state IN ('available', 'partial') AND state = 'available' THEN 0
                            WHEN root_state IN ('available', 'partial') AND state = 'missing' THEN 2
                            ELSE 1 END, root_id
                    ) AS preference
                    FROM files WHERE {where}
                ), labeled AS (
                    SELECT *, {membership} AS collection_names FROM ranked WHERE preference = 1
                )
                SELECT * FROM labeled
                ORDER BY {order} {direction}, volume, volume_path LIMIT ? OFFSET ?
                """,
                (*collections_args, os.sep, os.sep, *args, limit, offset),
            ).fetchall()

    def synchronize(self, collection, progress=None, *, root_id=None, on_progress=None):
        with self.mutation():
            roots = self.roots(collection)
            if root_id is not None:
                roots = [root for root in roots if root["id"] == root_id]
                if not roots:
                    raise ValueError("Cette racine n’existe plus dans la collection.")
            return self.scan_collection(collection, roots, progress, on_progress)

    def scan_collection(self, collection, roots, progress, on_progress):
        summary = Summary()
        now = time.time_ns()
        total = len(roots)
        for position, root in enumerate(roots, 1):
            root_path = root["path"]
            if progress is not None:
                progress(root_path)
            if on_progress is not None:
                on_progress(ScanProgress(root_path, position, total))
            with self.connect() as db:
                previous = {(row["relative"], row["kind"]): row for row in db.execute(
                    "SELECT * FROM entries WHERE root_id = ?", (root["id"],)
                )}
            try:
                source = verify(root["path"], root["volume"], root["relative"])
                def report_files(count):
                    on_progress(ScanProgress(root_path, position, total, count))

                scan = inventory(source, previous, report_files if on_progress is not None else None)
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
            fields = (entry.kind, entry.extension, entry.size, entry.modified, entry.title, entry.author,
                      entry.title_source, entry.author_source)
            state = "error" if scan.is_blocked(relative) else "available"
            rows.append((root["id"], relative, os.path.dirname(relative), entry.name,
                         key, *fields[:4], first, *fields[4:6], state, *fields[6:]))
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
                        "kind", "extension", "size", "modified", "title", "author",
                        "title_source", "author_source")):
                    summary.changed.add((root["volume"], key))

        db.executemany("INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
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
