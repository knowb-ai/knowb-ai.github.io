"""Export scoped documents as OKF and query the pinned Rust search adapter."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

from .index import IndexError


def bridge_path() -> str:
    configured = os.environ.get("KNOWB_OKF_BRIDGE")
    if configured:
        return str(Path(configured).expanduser())
    installed = shutil.which("knowb-okf-bridge")
    if installed:
        return installed
    return str(Path(__file__).resolve().parents[2] / "okf-bridge/target/release/knowb-okf-bridge")


def diagnostics() -> dict[str, Any]:
    binary = bridge_path()
    available = Path(binary).is_file() and os.access(binary, os.X_OK)
    return {"backend": "okf-rs", "binary": binary, "available": available}


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
    if not diagnostics()["available"]:
        raise IndexError(
            "okf-rs search adapter is missing. Build with: cargo build --release --locked "
            "--manifest-path mcp/okf-bridge/Cargo.toml; or set KNOWB_OKF_BRIDGE."
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
