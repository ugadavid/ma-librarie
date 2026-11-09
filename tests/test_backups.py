import os
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from catalogue import backups
from catalogue.store import Catalogue


@unittest.skipUnless(os.name == "nt", "Les verrous du catalogue utilisent Windows.")
class BackupTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.catalogue = Catalogue(self.root / "catalogue.sqlite3")
        self.collection = self.catalogue.create_collection("Livres", "books")
        self.destination = self.root / "Archives témoins.sqlite3"

    def session(self):
        session = backups.CatalogueSession(self.catalogue.filename)
        self.addCleanup(session.close)
        return session

    def prepare(self):
        backups.save_backup(self.catalogue, self.destination)
        prepared = backups.prepare_restore(self.catalogue, self.destination)
        self.addCleanup(prepared.close)
        return prepared

    def test_backup_is_standalone_and_preserves_previous_export_on_failure(self):
        with closing(sqlite3.connect(self.catalogue.filename)) as writer:
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("UPDATE collections SET name = 'Dernier commit' WHERE id = ?", (self.collection,))
            writer.commit()
            self.assertGreater(Path(str(self.catalogue.filename) + "-wal").stat().st_size, 0)
            backups.save_backup(self.catalogue, self.destination)

        isolated = self.root / "isolé"
        isolated.mkdir()
        only_file = isolated / "copie.sqlite3"
        shutil.copyfile(self.destination, only_file)
        with backups.read_only(only_file) as db:
            self.assertEqual("Dernier commit", db.execute("SELECT name FROM collections").fetchone()[0])
            self.assertEqual("delete", db.execute("PRAGMA journal_mode").fetchone()[0])
        self.assertEqual([only_file], list(isolated.iterdir()))
        original = self.destination.read_bytes()
        with patch.object(backups.os, "replace", side_effect=PermissionError("Refus témoin")):
            with self.assertRaises(PermissionError):
                backups.save_backup(self.catalogue, self.destination, overwrite=True)
        self.assertEqual(original, self.destination.read_bytes())
        self.assertEqual((1, 0), backups.validate(self.destination))
        with self.assertRaises(OSError):
            backups.save_backup(self.catalogue, self.root / "introuvable" / "copie.sqlite3")
        with self.assertRaisesRegex(backups.BackupError, "catalogue actif"):
            backups.save_backup(self.catalogue, self.catalogue.filename, overwrite=True)

    def test_restore_validates_origin_and_version(self):
        self.destination.write_bytes(b"fichier corrompu")
        with self.assertRaisesRegex(backups.BackupError, "corrompu"):
            backups.prepare_restore(self.catalogue, self.destination)
        self.destination.unlink()
        with closing(sqlite3.connect(self.destination)) as db:
            db.execute("CREATE TABLE etranger (id INTEGER)")
        with self.assertRaisesRegex(backups.BackupError, "sauvegarde de Ma Librarie"):
            backups.prepare_restore(self.catalogue, self.destination)
        with closing(sqlite3.connect(self.destination)) as db:
            db.execute(f"PRAGMA application_id = {backups.APPLICATION_ID}")
            db.execute("PRAGMA user_version = 99")
        with self.assertRaisesRegex(backups.BackupError, "version"):
            backups.prepare_restore(self.catalogue, self.destination)
        with closing(sqlite3.connect(self.destination)) as db:
            db.execute(f"PRAGMA user_version = {backups.BACKUP_VERSION}")
        with self.assertRaisesRegex(backups.BackupError, "schéma"):
            backups.prepare_restore(self.catalogue, self.destination)
        self.assertEqual("Livres", self.catalogue.collections()[0]["name"])

    def test_restore_recovers_after_failed_reopen_and_keeps_safety_copy(self):
        session = self.session()
        self.catalogue.save_results_view("mosaic")
        prepared = self.prepare()
        original_backup = self.destination.read_bytes()
        self.catalogue.rename_collection(self.collection, "Avant restauration")
        self.catalogue.save_results_view("detail")

        with patch.object(backups, "save_backup", side_effect=PermissionError("Refus témoin")):
            with self.assertRaisesRegex(backups.BackupError, "copie de sécurité"):
                backups.restore_backup(self.catalogue, prepared, session)
        self.assertFalse(list(self.root.glob("catalogue-avant-restauration-*")))
        with self.assertRaisesRegex(backups.BackupError, "autres instances"):
            other = backups.CatalogueSession(self.catalogue.filename)
            try:
                backups.restore_backup(self.catalogue, prepared, session)
            finally:
                other.close()
        self.assertFalse(list(self.root.glob("catalogue-avant-restauration-*")))

        reopen = backups.reopen
        calls = []

        def fail_once(path):
            calls.append(path)
            if len(calls) == 1:
                with backups.read_only(path) as db:
                    self.assertEqual("Livres", db.execute("SELECT name FROM collections").fetchone()[0])
                raise OSError("Échec de réouverture injecté")
            reopen(path)

        with patch.object(backups, "reopen", side_effect=fail_once):
            with self.assertRaisesRegex(backups.BackupError, "précédent est rouvert"):
                backups.restore_backup(self.catalogue, prepared, session)
        self.assertEqual("Avant restauration", Catalogue(self.catalogue.filename).collections()[0]["name"])
        self.assertEqual("detail", self.catalogue.results_view())
        self.assertEqual(2, len(calls))
        safety, = self.root.glob("catalogue-avant-restauration-*")
        self.assertEqual((1, 0), backups.validate(safety))
        with backups.read_only(safety) as db:
            self.assertEqual("Avant restauration", db.execute("SELECT name FROM collections").fetchone()[0])
        self.assertEqual(original_backup, self.destination.read_bytes())

        backups.restore_backup(self.catalogue, prepared, session)
        self.assertEqual("Livres", self.catalogue.collections()[0]["name"])
        self.assertEqual("mosaic", self.catalogue.results_view())
        self.assertEqual(original_backup, self.destination.read_bytes())
