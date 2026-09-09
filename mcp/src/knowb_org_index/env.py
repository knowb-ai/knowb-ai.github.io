"""Load an explicit environment file without overriding the parent environment.

Loading a project's `.env` merely because it was selected for reading is a
runtime checkout dependency. The default loader loads nothing: process
environment variables always win, and an explicit `KNOWB_ENV_FILE` is the only
file loaded by default. A documented legacy mode (`KNOWB_LEGACY_ENV=1`)
re-enables the old checkout-root `.env` behavior for migration.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path


_ASSIGNMENT = re.compile(r"^(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$")


class EnvironmentFileError(ValueError):
    """Raised when the local environment file contains an unsafe/malformed line."""


def default_env_path() -> Path | None:
    """Return the explicit env path, the legacy checkout path, or None.

    An explicit `KNOWB_ENV_FILE` always wins. Otherwise the legacy checkout
    path is used only when `KNOWB_LEGACY_ENV=1` is set. The default is no file,
    so an installed application never depends on a checkout layout.
    """

    explicit = os.environ.get("KNOWB_ENV_FILE", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    if os.environ.get("KNOWB_LEGACY_ENV", "").strip() in {"1", "true", "yes"}:
        root = os.environ.get("KNOWB_ORG_ROOT", "").strip()
        if root:
            return Path(root).expanduser().resolve() / ".env"
        return Path(__file__).resolve().parents[3] / ".env"
    return None


def _parse_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        if value[0] == "'":
            return value[1:-1]
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise EnvironmentFileError("Invalid double-quoted .env value") from exc
        if not isinstance(parsed, str):
            raise EnvironmentFileError(".env values must be strings")
        return parsed
    return value


def load_dotenv(path: str | Path | None = None) -> Path | None:
    """Load simple KEY=VALUE entries; existing process variables always win."""

    resolved = (
        Path(path).expanduser().resolve()
        if path
        else default_env_path()
    )
    if resolved is None or not resolved.is_file():
        return None
    try:
        lines = resolved.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EnvironmentFileError(f"Cannot read environment file: {resolved}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _ASSIGNMENT.fullmatch(line)
        if match is None:
            raise EnvironmentFileError(
                f"Invalid .env assignment at {resolved}:{line_number}"
            )
        key = match.group("key")
        value = _parse_value(match.group("value"))
        os.environ.setdefault(key, value)
    return resolved