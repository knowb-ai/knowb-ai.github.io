"""Load a repo-local .env file without overriding the parent environment."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path


_ASSIGNMENT = re.compile(r"^(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$")


class EnvironmentFileError(ValueError):
    """Raised when the local environment file contains an unsafe/malformed line."""


def default_env_path(*, legacy_checkout_root: Path | None = None) -> Path | None:
    """Return an explicitly selected env path or verified legacy checkout path."""

    explicit = os.environ.get("KNOWB_ENV_FILE", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    return legacy_checkout_root / ".env" if legacy_checkout_root else None


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


def load_dotenv(
    path: str | Path | None = None,
    *,
    legacy_checkout_root: Path | None = None,
) -> Path | None:
    """Load simple KEY=VALUE entries; existing process variables always win."""

    explicit = path is not None or bool(os.environ.get("KNOWB_ENV_FILE", "").strip())
    resolved = (
        Path(path).expanduser().resolve()
        if path
        else default_env_path(legacy_checkout_root=legacy_checkout_root)
    )
    if resolved is None:
        return None
    if not resolved.is_file():
        if explicit:
            raise EnvironmentFileError(f"Environment file does not exist: {resolved}")
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
