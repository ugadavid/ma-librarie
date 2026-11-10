import os
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .i18n import error_text, msg
from .store import CLASSIFICATION_SCHEMA, SCHEMA, SCHEMA_V1, SCHEMA_V2, WORK_SCHEMA


APPLICATION_ID = 0x4D4C4942  # MLIB
BACKUP_VERSION = 3
BACKUP_SCHEMAS = {1: SCHEMA_V1, 2: SCHEMA_V2, 3: SCHEMA}
SESSION_SLOTS = 32


class BackupError(ValueError):
    pass


def sessions_path(filename):
    return filename.with_suffix(filename.suffix + ".sessions")


class CatalogueSession:
    """One Windows byte lock per open application, released by the OS on exit."""

    def __init__(self, filename):
        import msvcrt

        self.msvcrt = msvcrt
        filename = Path(filename).resolve()
        filename.parent.mkdir(parents=True, exist_ok=True)
        self.file = sessions_path(filename).open("a+b")
        for slot in range(SESSION_SLOTS):
            try:
                self.lock(slot, 1, msvcrt.LK_NBLCK)
            except OSError:
                continue
            self.slot = slot
            break
        else:
            self.close()
            raise BackupError(msg("catalogue_occupe_par_une_restauration_ou_trop"))

    def lock(self, start, size, mode):
        self.file.seek(start)
        self.msvcrt.locking(self.file.fileno(), mode, size)

    @contextmanager
    def exclusive(self):
        acquired = []
        try:
            for start, size in ((0, self.slot), (self.slot + 1, SESSION_SLOTS - self.slot - 1)):
                if not size:
                    continue
                try:
                    self.lock(start, size, self.msvcrt.LK_NBLCK)
                except OSError as exc:
                    raise BackupError(msg("fermez_les_autres_instances_de_ma_librarie")) from exc
                acquired.append((start, size))
            yield
        finally:
            for start, size in reversed(acquired):
                self.lock(start, size, self.msvcrt.LK_UNLCK)

    def close(self):
        self.file.close()


@dataclass(frozen=True)
class PreparedBackup:
    path: Path
    name: str
    collections: int
    roots: int

    def close(self):
        self.path.unlink(missing_ok=True)


def temporary_database(directory):
    fd, name = tempfile.mkstemp(prefix=".ma-librarie-", suffix=".sqlite3", dir=Path(directory).resolve())
    os.close(fd)
    return Path(name)


def protect_active(catalogue, path):
    live = catalogue.filename.resolve()
    path = Path(path).resolve()
    for reserved in (live, sessions_path(live),
                     *(Path(str(live) + suffix) for suffix in ("-wal", "-shm", "-journal", ".lock"))):
        if path == reserved or (path.exists() and reserved.exists() and path.samefile(reserved)):
            raise BackupError(msg("choisissez_un_autre_fichier_que_le_catalogue"))
    return path


@contextmanager
def read_only(path):
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0)) as db:
        db.execute("PRAGMA trusted_schema = OFF")
        db.execute("PRAGMA query_only = ON")
        yield db


def copy_sqlite(source, target):
    def progress(status, _remaining, _total):
        if status in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            raise BackupError(msg("le_fichier_sqlite_est_occupe"))

    source.backup(target, pages=256, progress=progress)


def schema_signature(db):
    objects = db.execute(
        """SELECT type, name FROM sqlite_master
           WHERE name NOT GLOB 'sqlite_*' ORDER BY type, name"""
    ).fetchall()
    if any(kind not in ("table", "index") for kind, _ in objects):
        raise BackupError(msg("le_schema_de_la_sauvegarde_est_incompatible"))
    tables = {}
    for kind, name in objects:
        if kind != "table":
            continue
        columns = tuple(db.execute("SELECT * FROM pragma_table_xinfo(?)", (name,)))
        keys = tuple(db.execute("SELECT * FROM pragma_foreign_key_list(?)", (name,)))
        indexes = {}
        for _, index, unique, origin, partial in db.execute("SELECT * FROM pragma_index_list(?)", (name,)):
            indexes[index] = unique, origin, partial, tuple(
                db.execute("SELECT * FROM pragma_index_xinfo(?)", (index,))
            )
        tables[name] = columns, keys, indexes
    return objects, tables


def validate(path, *, backup=True):
    version = BACKUP_VERSION
    with read_only(path) as db:
        if backup:
            if db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
                raise BackupError(msg("ce_fichier_nest_pas_une_sauvegarde_de_ma"))
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in BACKUP_SCHEMAS:
                raise BackupError(msg("cette_version_de_sauvegarde_nest_pas_prise_en"))
        with closing(sqlite3.connect(":memory:")) as expected:
            expected.executescript(BACKUP_SCHEMAS[version])
            if schema_signature(db) != schema_signature(expected):
                raise BackupError(msg("le_schema_de_la_sauvegarde_est_incompatible"))
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise BackupError(msg("le_catalogue_sqlite_est_corrompu"))
        if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise BackupError(msg("le_catalogue_contient_des_references_invalides"))
        return tuple(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                     for table in ("collections", "roots"))


def stage_snapshot(source_path, target_path, *, mark_backup=False):
    with read_only(source_path) as source, closing(sqlite3.connect(target_path, timeout=0)) as target:
        copy_sqlite(source, target)
        if target.execute("PRAGMA journal_mode = DELETE").fetchone()[0] != "delete":
            raise BackupError(msg("impossible_de_preparer_un_fichier_de_sauvegarde"))
        if mark_backup:
            target.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            target.execute(f"PRAGMA user_version = {BACKUP_VERSION}")


def require_standalone(path):
    if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise BackupError(msg("le_fichier_a_des_journaux_sqlite_fermez_la_base"))


def save_backup(catalogue, destination, *, overwrite=False):
    destination = protect_active(catalogue, destination)
    require_standalone(destination)
    temporary = temporary_database(destination.parent)
    try:
        stage_snapshot(catalogue.filename.resolve(), temporary, mark_backup=True)
        validate(temporary)
        require_standalone(destination)
        if overwrite:
            os.replace(temporary, destination)
        else:
            # On Windows rename fails if the destination appeared in the meantime.
            temporary.rename(destination)
        return destination
    finally:
        temporary.unlink(missing_ok=True)


def prepare_restore(catalogue, source):
    source = protect_active(catalogue, source)
    require_standalone(source)
    temporary = temporary_database(catalogue.filename.parent)
    try:
        with source.open("rb") as stream:
            header = stream.read(20)
        if not header.startswith(b"SQLite format 3\0"):
            raise BackupError(msg("fichier_sqlite_illisible_ou_corrompu"))
        if header[18:20] != b"\x01\x01":
            raise BackupError(msg("la_sauvegarde_doit_etre_un_fichier_sqlite"))
        stage_snapshot(source, temporary)
        collections, roots = validate(temporary)
        with closing(sqlite3.connect(temporary)) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version < BACKUP_VERSION:
                migration = CLASSIFICATION_SCHEMA + WORK_SCHEMA if version == 1 else WORK_SCHEMA
                db.executescript(migration)
                db.execute(f"PRAGMA user_version = {BACKUP_VERSION}")
        validate(temporary)
        return PreparedBackup(temporary, source.name, collections, roots)
    except sqlite3.DatabaseError as exc:
        temporary.unlink(missing_ok=True)
        raise BackupError(msg("backup_unreadable", error=error_text(exc))) from exc
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def switch_journal(path, mode):
    with closing(sqlite3.connect(path, timeout=0)) as db:
        if db.execute(f"PRAGMA journal_mode = {mode}").fetchone()[0] != mode.lower():
            raise BackupError(msg("impossible_dobtenir_lacces_requis_au_catalogue"))


def replace_contents(source, live):
    with read_only(source) as origin, closing(sqlite3.connect(live, timeout=0)) as target:
        copy_sqlite(origin, target)


def reopen(live):
    validate(live, backup=False)
    switch_journal(live, "WAL")


def restore_backup(catalogue, prepared, session):
    live = catalogue.filename.resolve()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safety = live.with_name(f"catalogue-avant-restauration-{stamp}-{uuid4().hex[:8]}.sqlite3")
    with session.exclusive(), catalogue.mutation():
        validate(prepared.path)
        try:
            save_backup(catalogue, safety)
        except (OSError, sqlite3.Error, BackupError) as exc:
            raise BackupError(msg("safety_copy_error", error=error_text(exc))) from exc
        switched = False
        try:
            # SQLite checkpoints the old WAL and owns the replacement transaction.
            switch_journal(live, "DELETE")
            switched = True
            replace_contents(prepared.path, live)
            reopen(live)
        except (OSError, sqlite3.Error, BackupError) as exc:
            if switched:
                try:
                    switch_journal(live, "DELETE")
                    replace_contents(safety, live)
                    reopen(live)
                except (OSError, sqlite3.Error, BackupError) as recovery:
                    raise BackupError(
                        msg("restore_reopen_error", path=safety, error=error_text(recovery))
                    ) from exc
                raise BackupError(
                    msg("restore_previous_reopened", path=safety, error=error_text(exc))
                ) from exc
            raise BackupError(
                msg("restore_interrupted", path=safety, error=error_text(exc))
            ) from exc
    return safety
