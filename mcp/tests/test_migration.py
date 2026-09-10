import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from backup_sqlite import BackupError, backup_database


class MigrationSafetyTests(unittest.TestCase):
    def test_online_backup_preserves_schema_ledger_counts_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "org-index.sqlite"
            with sqlite3.connect(source) as connection:
                connection.executescript(
                    """
                    CREATE TABLE documents (id INTEGER PRIMARY KEY, content TEXT);
                    CREATE TABLE pending_actions (token TEXT PRIMARY KEY);
                    CREATE TABLE audit_events (audit_id TEXT PRIMARY KEY);
                    INSERT INTO documents VALUES (1, 'private content');
                    INSERT INTO pending_actions VALUES ('pending-token');
                    INSERT INTO audit_events VALUES ('audit-1');
                    """
                )
            result = backup_database(source, root / "backup" / "org-index.sqlite")
            self.assertEqual(result["integrity"], "ok")
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(
                result["table_counts"],
                {"documents": 1, "pending_actions": 1, "audit_events": 1},
            )
            with sqlite3.connect(result["destination"]) as connection:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM pending_actions").fetchone()[0], 1)

    def test_backup_refuses_in_place_or_accidental_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "state.sqlite"
            sqlite3.connect(source).close()
            with self.assertRaisesRegex(BackupError, "must differ"):
                backup_database(source, source)
            destination = Path(directory) / "backup.sqlite"
            backup_database(source, destination)
            with self.assertRaisesRegex(BackupError, "already exists"):
                backup_database(source, destination)


if __name__ == "__main__":
    unittest.main()
