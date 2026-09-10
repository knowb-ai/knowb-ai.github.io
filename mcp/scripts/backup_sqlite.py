#!/usr/bin/env python3
"""Create and inspect a SQLite online backup for connector migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


class BackupError(ValueError):
    """Raised when a connector state backup cannot be completed safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    counts: dict[str, int] = {}
    for table in ("documents", "pending_actions", "audit_events"):
        if table in tables:
            counts[table] = int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    return counts


def backup_database(
    source: str | Path,
    destination: str | Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Back up a stopped connector database using SQLite's online API."""

    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()
    if not source_path.is_file():
        raise BackupError(f"Source database does not exist: {source_path}")
    if source_path == destination_path:
        raise BackupError("Source and destination databases must differ")
    if destination_path.exists() and not force:
        raise BackupError(
            f"Backup already exists: {destination_path}. Pass --force to replace it."
        )
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists():
        destination_path.unlink()

    try:
        source_connection = sqlite3.connect(
            f"file:{source_path.as_posix()}?mode=ro", uri=True, timeout=15
        )
        destination_connection = sqlite3.connect(destination_path, timeout=15)
        try:
            source_connection.execute("PRAGMA query_only = ON")
            source_connection.backup(destination_connection)
            destination_connection.commit()
            integrity = destination_connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise BackupError(f"Backup integrity check failed: {integrity}")
            tables = {
                row[0]
                for row in destination_connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            schema_version = 1 if "documents" in tables else 0
            counts = _table_counts(destination_connection)
        finally:
            destination_connection.close()
            source_connection.close()
    except (OSError, sqlite3.Error) as exc:
        if destination_path.exists():
            destination_path.unlink()
        raise BackupError(f"SQLite backup failed: {exc}") from exc

    return {
        "source": str(source_path),
        "destination": str(destination_path),
        "sha256": _sha256(destination_path),
        "bytes": destination_path.stat().st_size,
        "integrity": "ok",
        "schema_version": schema_version,
        "table_counts": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        result = backup_database(args.source, args.destination, force=args.force)
    except (BackupError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
