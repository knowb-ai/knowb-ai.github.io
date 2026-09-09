"""Export scoped documents as OKF and query the pinned Rust search adapter.

The adapter is bundled inside the installed package at
`knowb_org_index/_bin/knowb-okf-bridge`. An explicit `KNOWB_OKF_BRIDGE`
override is accepted for development builds and must be an absolute path.
Ambient PATH preference is intentionally removed so an unrelated stale
binary cannot replace the packaged version.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

from .index import IndexError


_ADAPTER_NAME = "knowb-okf-bridge.exe" if os.name == "nt" else "knowb-okf-bridge"


def _bundled_adapter() -> Path:
    """Return the adapter shipped inside the installed package, if present."""

    try:
        files = importlib_resources.files("knowb_org_index") / "_bin" / _ADAPTER_NAME
        with importlib_resources.as_file(files) as path:
            return Path(path)
    except (ModuleNotFoundError, FileNotFoundError):
        return Path(__file__).resolve().parent / "_bin" / _ADAPTER_NAME


def _dev_fallback() -> Path | None:
    """A documented fallback for development checkouts only.

    The bundled adapter is always preferred. When it is absent and the
    application is running from a checkout (a repository root was found),
    fall back to the checked-in build path so developers can run the
    real-engine tests without setting an override. Installed wheels never
    reach this path: they ship the adapter inside the package.
    """

    from .config import _find_repository_root

    root = _find_repository_root()
    if root is None:
        return None
    candidate = root / "mcp" / "okf-bridge" / "target" / "release" / _ADAPTER_NAME
    return candidate if candidate.is_file() else None


def bridge_path() -> str:
    """Resolve the active okf-rs adapter.

    Order: an explicit absolute override, then the bundled package resource,
    then a documented development fallback to the checkout build path. An
    ambient PATH lookup is deliberately not consulted so a stale, unrelated
    binary can never shadow the shipped adapter.
    """

    configured = os.environ.get("KNOWB_OKF_BRIDGE", "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            raise IndexError(
                "KNOWB_OKF_BRIDGE must be an absolute executable path"
            )
        return str(path)
    bundled = _bundled_adapter()
    if bundled.is_file():
        return str(bundled)
    fallback = _dev_fallback()
    if fallback is not None:
        return str(fallback)
    return str(bundled)


def _bridge_version() -> str:
    """Return the adapter's self-reported version, or '' if it cannot run."""

    binary = bridge_path()
    try:
        result = subprocess.run(
            [binary, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()


def diagnostics() -> dict[str, Any]:
    binary = bridge_path()
    available = Path(binary).is_file() and os.access(binary, os.X_OK)
    version = _bridge_version() if available else ""
    return {
        "backend": "okf-rs",
        "binary": binary,
        "available": available,
        "version": version,
        "protocol": 1 if version else 0,
    }


def _protocol_mismatch(diag: dict[str, Any]) -> bool:
    """A bundled adapter must speak protocol 1; an override may be anything."""

    if os.environ.get("KNOWB_OKF_BRIDGE", "").strip():
        return False
    return bool(diag.get("protocol")) and diag["protocol"] != 1


def search_documents(
    documents: list[dict[str, Any]], query: str, limit: int, state_dir: Path,
) -> list[dict[str, Any]]:
    """One scoped bundle gives all selected projects comparable BM25 scores."""

    if not query.strip():
        raise IndexError("query cannot be empty")
    if len(query.encode("utf-8")) > 16384:
        raise IndexError("query exceeds 16 KiB")
    if not documents:
        return []
    binary = bridge_path()
    diag = diagnostics()
    if not diag["available"]:
        raise IndexError(
            "okf-rs search adapter is missing. Install the platform wheel or "
            "set KNOWB_OKF_BRIDGE to an absolute executable path."
        )
    if _protocol_mismatch(diag):
        raise IndexError(
            "okf-rs adapter protocol mismatch; reinstall the packaged connector."
        )
    limit = max(1, min(limit, 50))
    # Per-call private snapshots isolate simultaneous requests and never include
    # unselected projects, disabled repositories, or arbitrary source files.
    with tempfile.TemporaryDirectory(prefix="okf-", dir=state_dir) as directory:
        bundle = Path(directory)
        identities: dict[str, dict[str, Any]] = {}
        for doc in documents:
            identity = hashlib.sha256(
                json.dumps([doc["project_id"], doc["relative_path"]]).encode()
            ).hexdigest()
            identities[identity] = doc
            metadata = {
                "type": "DITA Document", "title": doc["title"],
                "resource": Path(doc["source_path"]).as_uri(),
                "generated": {"by": "knowb-org-index/okf-export-1"},
                "knowb_project": doc["project_id"], "knowb_path": doc["relative_path"],
            }
            (bundle / f"{identity}.md").write_text(
                "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
                + "---\n" + doc["content"], encoding="utf-8",
            )
        (bundle / "index.md").write_text(
            '---\nokf_version: "0.2"\n---\n\n# KnowB search snapshot\n\n'
            + "\n".join(f"- [{key}]({key}.md)" for key in identities) + "\n",
            encoding="utf-8",
        )
        request = json.dumps({"bundle": directory, "query": query, "limit": limit, "documents": len(documents)})
        try:
            result = subprocess.run(
                [binary], input=request, text=True, capture_output=True, timeout=60,
                cwd=directory, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise IndexError("okf-rs adapter unavailable or timed out") from exc
        if result.returncode:
            # Never echo source-bearing diagnostics to an unrelated tool caller.
            raise IndexError("okf-rs search failed; check the adapter build and bundle compatibility")
        try:
            response = json.loads(result.stdout)
            hits = response["results"]
            if response["protocol"] != 1 or not isinstance(hits, list) or len(hits) > limit:
                raise ValueError("invalid protocol")
            results = []
            seen = set()
            for hit in hits:
                identity = hit["id"]
                if identity in seen:
                    raise ValueError("duplicate result")
                seen.add(identity)
                doc = identities[identity]
                score = float(hit["score"])
                if not math.isfinite(score):
                    raise ValueError("invalid score")
                terms = re.findall(r"\w+", query.casefold())
                positions = [doc["content"].casefold().find(term) for term in terms]
                start = max(0, min((p for p in positions if p >= 0), default=0) - 100)
                excerpt = doc["content"][start:start + 500]
                results.append({
                    "project": doc["project_id"], "path": doc["relative_path"],
                    "title": doc["title"], "headings": doc["headings"].splitlines(),
                    "excerpt": excerpt, "score": score, "source_path": doc["source_path"],
                    "uri": f"knowb://project/{quote(doc['project_id'], safe='')}/doc/{quote(doc['relative_path'])}",
                    "indexed_at": doc["indexed_at"], "backend": "okf-rs",
                })
            return results
        except (ValueError, KeyError, TypeError) as exc:
            raise IndexError("Invalid response from okf-rs adapter") from exc