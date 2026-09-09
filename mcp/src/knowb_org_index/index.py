"""Incremental local document index and durable action audit store."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import quote

from .models import Project, Registry


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_IGNORED_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "node_modules",
    "target",
    "dist",
    "build",
    "__pycache__",
}


class IndexError(ValueError):
    """Raised for invalid index/search/document operations."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _matches(path: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        normalized = pattern.replace("\\", "/").lstrip("./")
        if fnmatch.fnmatchcase(path, normalized):
            return True
        if normalized.startswith("**/") and fnmatch.fnmatchcase(path, normalized[3:]):
            return True
    return False


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


class LocalIndex:
    """A document snapshot and audit cache; okf-rs supplies ranked retrieval."""

    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        self.registry.state_dir.mkdir(parents=True, exist_ok=True)
        self.path = registry.database_path
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 15000")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    remote TEXT,
                    status TEXT NOT NULL,
                    indexed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS documents (
                    project_id TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    headings TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    modified_ns INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    PRIMARY KEY (project_id, relative_path)
                );

                CREATE TABLE IF NOT EXISTS pending_actions (
                    token TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    preview_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    result_json TEXT
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    audit_id TEXT PRIMARY KEY,
                    token TEXT,
                    event TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _candidate_files(self, project: Project) -> dict[str, Path]:
        project_root = project.path.resolve()
        files: dict[str, Path] = {}
        for source in project.sources:
            raw_root = project_root / source.path
            if any(parent.is_symlink() for parent in (raw_root, *raw_root.parents)
                   if parent != project_root and _within(parent, project_root)):
                continue
            source_root = raw_root.resolve()
            if not _within(source_root, project_root) or not source_root.is_dir():
                continue
            try:
                iterator = source_root.rglob("*")
                for candidate in iterator:
                    if (any(parent.is_symlink() for parent in (candidate, *candidate.parents)
                            if parent != project_root and _within(parent, project_root))
                            or not candidate.is_file()):
                        continue
                    resolved = candidate.resolve()
                    if not _within(resolved, project_root):
                        continue
                    source_relative = resolved.relative_to(source_root).as_posix()
                    project_relative = resolved.relative_to(project_root).as_posix()
                    if any(part in _IGNORED_PARTS for part in resolved.relative_to(project_root).parts):
                        continue
                    if not _matches(source_relative, source.include):
                        continue
                    if _matches(source_relative, source.exclude):
                        continue
                    if _matches(project_relative, self.registry.forbidden_paths):
                        continue
                    try:
                        if resolved.stat().st_size > self.registry.max_file_bytes:
                            continue
                    except OSError:
                        continue
                    files[project_relative] = (project.path / project_relative).resolve()
            except OSError:
                continue
        return files

    @staticmethod
    def _document_metadata(path: Path, content: str) -> tuple[str, str]:
        headings = [match.group(2).strip() for match in _HEADING.finditer(content)]
        title = headings[0] if headings else path.stem.replace("-", " ").replace("_", " ")
        return title, "\n".join(headings)

    def refresh_project(self, project: Project) -> dict[str, Any]:
        """Incrementally refresh one registered project from local files only."""

        if not project.active:
            with self._connect() as connection:
                connection.execute("DELETE FROM documents WHERE project_id = ?", (project.id,))
                connection.execute("DELETE FROM projects WHERE project_id = ?", (project.id,))
            return {
                "project": project.id,
                "status": project.status,
                "indexed": 0,
                "unchanged": 0,
                "deleted": 0,
            }

        candidates = self._candidate_files(project)
        indexed = 0
        unchanged = 0
        deleted = 0
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects(project_id, name, path, remote, status, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name=excluded.name,
                    path=excluded.path,
                    remote=excluded.remote,
                    status=excluded.status,
                    indexed_at=excluded.indexed_at
                """,
                (project.id, project.name, str(project.path), project.remote, project.status, now),
            )
            existing = {
                row["relative_path"]: row
                for row in connection.execute(
                    """
                    SELECT relative_path, content_hash, modified_ns, size_bytes
                    FROM documents WHERE project_id = ?
                    """,
                    (project.id,),
                )
            }

            for relative_path, source_path in candidates.items():
                try:
                    stat = source_path.stat()
                except OSError:
                    continue
                previous = existing.get(relative_path)
                if (
                    previous
                    and previous["modified_ns"] == stat.st_mtime_ns
                    and previous["size_bytes"] == stat.st_size
                ):
                    unchanged += 1
                    continue

                try:
                    raw = source_path.read_bytes()
                except OSError:
                    continue
                digest = hashlib.sha256(raw).hexdigest()
                if previous and previous["content_hash"] == digest:
                    connection.execute(
                        """
                        UPDATE documents SET modified_ns = ?, size_bytes = ?, indexed_at = ?
                        WHERE project_id = ? AND relative_path = ?
                        """,
                        (stat.st_mtime_ns, stat.st_size, now, project.id, relative_path),
                    )
                    unchanged += 1
                    continue

                content = raw.decode("utf-8", errors="replace")
                title, headings = self._document_metadata(source_path, content)
                connection.execute(
                    """
                    INSERT INTO documents(
                        project_id, relative_path, source_path, title, headings, content,
                        content_hash, modified_ns, size_bytes, indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, relative_path) DO UPDATE SET
                        source_path=excluded.source_path,
                        title=excluded.title,
                        headings=excluded.headings,
                        content=excluded.content,
                        content_hash=excluded.content_hash,
                        modified_ns=excluded.modified_ns,
                        size_bytes=excluded.size_bytes,
                        indexed_at=excluded.indexed_at
                    """,
                    (
                        project.id,
                        relative_path,
                        str(source_path),
                        title,
                        headings,
                        content,
                        digest,
                        stat.st_mtime_ns,
                        stat.st_size,
                        now,
                    ),
                )
                indexed += 1

            for relative_path in set(existing) - set(candidates):
                connection.execute(
                    "DELETE FROM documents WHERE project_id = ? AND relative_path = ?",
                    (project.id, relative_path),
                )
                deleted += 1

        return {
            "project": project.id,
            "status": project.status,
            "indexed": indexed,
            "unchanged": unchanged,
            "deleted": deleted,
            "documents": len(candidates),
        }

    def search(
        self,
        query: str,
        *,
        project_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search indexed local knowledge with source citations."""

        from .okf import search_documents

        selected = set(project_ids) if project_ids is not None else None
        active = [project.id for project in self.registry.projects
                  if project.active and (selected is None or project.id in selected)]
        if not active:
            if not query.strip():
                raise IndexError("query cannot be empty")
            return []
        with self._connect() as connection:
            placeholders = ",".join("?" for _ in active)
            documents = [dict(row) for row in connection.execute(
                f"SELECT * FROM documents WHERE project_id IN ({placeholders}) "
                "ORDER BY project_id, relative_path", active,
            )]
        return search_documents(documents, query, limit, self.registry.state_dir)

    def get_document(self, project_id: str, relative_path: str) -> dict[str, Any] | None:
        normalized = Path(relative_path).as_posix().lstrip("/")
        if not normalized or ".." in Path(normalized).parts:
            raise IndexError("Document path must be project-relative and cannot contain '..'")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT project_id, relative_path, source_path, title, headings,
                       content, content_hash, indexed_at
                FROM documents WHERE project_id = ? AND relative_path = ?
                """,
                (project_id, normalized),
            ).fetchone()
        if row is None:
            return None
        return {
            "project": row["project_id"],
            "path": row["relative_path"],
            "source_path": row["source_path"],
            "title": row["title"],
            "headings": [item for item in row["headings"].splitlines() if item],
            "content": row["content"],
            "content_hash": row["content_hash"],
            "uri": f"knowb://project/{quote(project_id, safe='')}/doc/{quote(normalized)}",
            "indexed_at": row["indexed_at"],
        }

    def list_documents(self, project_id: str, limit: int = 250) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT relative_path, source_path, title, headings, indexed_at
                FROM documents WHERE project_id = ?
                ORDER BY relative_path LIMIT ?
                """,
                (project_id, max(1, min(limit, 1000))),
            ).fetchall()
        return [
            {
                "path": row["relative_path"],
                "source_path": row["source_path"],
                "title": row["title"],
                "headings": [item for item in row["headings"].splitlines() if item],
                "indexed_at": row["indexed_at"],
            }
            for row in rows
        ]

    def project_stats(self, project_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS document_count, MAX(indexed_at) AS latest_document_at
                FROM documents WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
            project_row = connection.execute(
                "SELECT indexed_at FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        documents = int(row["document_count"]) if row else 0
        indexed_at = project_row["indexed_at"] if project_row else None
        return {
            "documents": documents,
            "indexed_at": indexed_at,
            "latest_document_at": row["latest_document_at"] if row else None,
            "status": "indexed" if indexed_at is not None else "not_indexed",
            "refresh_policy": "incremental_on_index/search/read/context",
        }

    def create_pending_action(
        self,
        *,
        kind: str,
        payload: dict[str, Any],
        preview: dict[str, Any],
        idempotency_key: str | None = None,
        ttl_seconds: int = 900,
    ) -> dict[str, Any]:
        now = _utc_now()
        expires_at = int(time.time()) + max(60, min(ttl_seconds, 3600))
        with self._connect() as connection:
            if idempotency_key:
                existing = connection.execute(
                    "SELECT * FROM pending_actions WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing is not None:
                    return self._pending_row(existing)
            token = secrets.token_urlsafe(24)
            connection.execute(
                """
                INSERT INTO pending_actions(
                    token, idempotency_key, kind, payload_json, preview_json,
                    status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    token,
                    idempotency_key,
                    kind,
                    json.dumps(payload, sort_keys=True),
                    json.dumps(preview, sort_keys=True),
                    now,
                    expires_at,
                ),
            )
            self._insert_audit(connection, token, "proposed", kind, preview)
            row = connection.execute(
                "SELECT * FROM pending_actions WHERE token = ?", (token,)
            ).fetchone()
        if row is None:
            raise IndexError("Failed to persist pending action")
        return self._pending_row(row)

    def get_pending_action(self, token: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM pending_actions WHERE token = ?", (token,)
            ).fetchone()
        return self._pending_row(row) if row else None

    def claim_pending_action(self, token: str) -> tuple[dict[str, Any] | None, bool]:
        """Atomically claim a pending mutation so concurrent confirms cannot duplicate it."""

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM pending_actions WHERE token = ?", (token,)
            ).fetchone()
            if row is None:
                return None, False
            pending = self._pending_row(row)
            if pending["status"] != "pending" or pending["expired"]:
                return pending, False
            updated = connection.execute(
                """
                UPDATE pending_actions SET status = 'executing'
                WHERE token = ? AND status = 'pending'
                """,
                (token,),
            ).rowcount
            if updated != 1:
                refreshed = connection.execute(
                    "SELECT * FROM pending_actions WHERE token = ?", (token,)
                ).fetchone()
                return (self._pending_row(refreshed) if refreshed else None), False
            self._insert_audit(
                connection,
                token,
                "confirmed",
                pending["kind"],
                {"preview": pending["preview"]},
            )
            pending["status"] = "executing"
            return pending, True

    @staticmethod
    def _pending_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "token": row["token"],
            "idempotency_key": row["idempotency_key"],
            "kind": row["kind"],
            "payload": json.loads(row["payload_json"]),
            "preview": json.loads(row["preview_json"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "expires_at": datetime.fromtimestamp(row["expires_at"], UTC).isoformat(),
            "expired": row["expires_at"] < int(time.time()),
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
        }

    def finish_pending_action(
        self,
        token: str,
        *,
        status: str,
        result: dict[str, Any],
    ) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT kind FROM pending_actions WHERE token = ?", (token,)
            ).fetchone()
            if row is None:
                raise IndexError("Unknown confirmation token")
            connection.execute(
                "UPDATE pending_actions SET status = ?, result_json = ? WHERE token = ?",
                (status, json.dumps(result, sort_keys=True), token),
            )
            return self._insert_audit(connection, token, status, row["kind"], result)

    @staticmethod
    def _insert_audit(
        connection: sqlite3.Connection,
        token: str | None,
        event: str,
        kind: str,
        detail: dict[str, Any],
    ) -> str:
        audit_id = str(uuid.uuid4())
        connection.execute(
            """
            INSERT INTO audit_events(audit_id, token, event, kind, detail_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (audit_id, token, event, kind, json.dumps(detail, sort_keys=True), _utc_now()),
        )
        return audit_id

    def audit_log(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT audit_id, token, event, kind, detail_json, created_at
                FROM audit_events ORDER BY created_at DESC LIMIT ?
                """,
                (max(1, min(limit, 200)),),
            ).fetchall()
        return [
            {
                "audit_id": row["audit_id"],
                "token": row["token"],
                "event": row["event"],
                "kind": row["kind"],
                "detail": json.loads(row["detail_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
