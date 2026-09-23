"""Formal, non-persistent review of memo drafts and their source references."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Callable
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlsplit


MEMO_KINDS = frozenset({"memo", "decision", "plan", "project_direction", "brief", "research"})
MAX_TITLE_CHARS = 256
MAX_DRAFT_BYTES = 65_536
MAX_PURPOSE_CHARS = 2_000
MAX_SCOPE_CHARS = 4_000
MAX_NEXT_ACTIONS = 20
MAX_ACTION_CHARS = 1_000
MAX_RELATED_PATHS = 50
MAX_EXTERNAL_SOURCES = 50
_CANONICALIZATION = (
    "Unicode NFC; CRLF and CR become LF; outer whitespace is trimmed; "
    "JSON uses sorted keys and compact separators encoded as UTF-8"
)


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def _text(value: Any) -> str:
    return _normalize(value) if isinstance(value, str) else ""


def _local_path(value: Any) -> str | None:
    raw = _text(value)
    if not raw or len(raw) > 2_048 or "\\" in raw or "\x00" in raw or not raw.isprintable():
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw.split("/")):
        return None
    return path.as_posix()


def _external_source(value: Any) -> dict[str, str] | None:
    url = _text(value)
    if not url or len(url) > 8_192 or any(ch.isspace() for ch in url) or not url.isprintable():
        return None
    try:
        parts = urlsplit(url)
        # Reading URLs is deliberately out of scope: this is syntax validation only.
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme.casefold() not in {"http", "https"}
        or not parts.netloc
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or (port is not None and not 1 <= port <= 65535)
    ):
        return None
    return {"url": url, "title": parts.hostname, "validation": "URL syntax only; not fetched"}


def review_memo(
    *,
    project: str = "",
    title: str = "",
    memo_kind: str = "",
    draft: str = "",
    purpose: str = "",
    scope: str = "",
    next_actions: list[str] | None = None,
    open_questions_reviewed: bool = False,
    related_paths: list[str] | None = None,
    external_sources: list[str] | None = None,
    project_check: Callable[[str], tuple[bool, str]] | None = None,
    read_document: Callable[[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return checklist, source citations, and a deterministic content digest.

    This function never stores or returns the draft. The caller owns recording and
    must obtain user approval for the digest before doing so.
    """

    clean_project = _text(project)
    clean_title = _text(title)
    clean_kind = _text(memo_kind)
    clean_draft = _normalize(draft) if isinstance(draft, str) else ""
    clean_purpose = _text(purpose)
    clean_scope = _text(scope)
    actions = [_text(item) for item in next_actions] if isinstance(next_actions, list) else []
    paths_are_list = related_paths is None or isinstance(related_paths, list)
    urls_are_list = external_sources is None or isinstance(external_sources, list)
    paths = related_paths if isinstance(related_paths, list) else []
    urls = external_sources if isinstance(external_sources, list) else []

    checks: list[dict[str, Any]] = []
    questions: list[str] = []

    def check(name: str, passed: bool, detail: str, question: str | None = None) -> None:
        checks.append({"name": name, "status": "passed" if passed else "needs_refinement", "detail": detail})
        if not passed and question:
            questions.append(question)

    check("project", bool(clean_project), "A registered project is required.", "Choose the registered project this memo belongs to.")
    if clean_project and project_check:
        try:
            project_ok, project_detail = project_check(clean_project)
        except ValueError as exc:  # Project lookup errors become review feedback, not a server error.
            project_ok, project_detail = False, str(exc)
        check("project_access", project_ok, project_detail, "Select an active registered project and retry the review.")
    elif clean_project:
        check("project_access", True, "Project access check was not configured.")

    check("title", bool(clean_title) and len(clean_title) <= MAX_TITLE_CHARS,
          f"Title must contain 1-{MAX_TITLE_CHARS} characters.", "Add a concise title within the size limit.")
    check("memo_kind", clean_kind in MEMO_KINDS,
          f"Memo kind must be one of: {', '.join(sorted(MEMO_KINDS))}.", "Choose a supported memo kind.")
    try:
        draft_size = len(clean_draft.encode("utf-8"))
    except UnicodeEncodeError:
        draft_size = MAX_DRAFT_BYTES + 1
    check("draft", bool(clean_draft) and draft_size <= MAX_DRAFT_BYTES,
          f"Draft must contain text and be no larger than {MAX_DRAFT_BYTES} UTF-8 bytes.", "Add or reduce the memo draft so it fits the size limit.")
    check("purpose", bool(clean_purpose) and len(clean_purpose) <= MAX_PURPOSE_CHARS,
          f"Purpose must contain 1-{MAX_PURPOSE_CHARS} characters.", "State what this memo is intended to establish.")
    check("scope", bool(clean_scope) and len(clean_scope) <= MAX_SCOPE_CHARS,
          f"Scope must contain 1-{MAX_SCOPE_CHARS} characters.", "State what this memo covers and the boundary of its claims.")
    valid_actions = bool(actions) and len(actions) <= MAX_NEXT_ACTIONS and all(
        action and len(action) <= MAX_ACTION_CHARS for action in actions
    )
    check("next_actions", valid_actions,
          f"Provide 1-{MAX_NEXT_ACTIONS} non-empty next actions, each no longer than {MAX_ACTION_CHARS} characters.",
          "Add at least one concrete next action.")
    questions_ok = isinstance(open_questions_reviewed, bool) and open_questions_reviewed
    check("open_questions_reviewed", questions_ok,
          "Unresolved questions were explicitly reviewed." if questions_ok else "Confirm that open questions were reviewed.",
          "Review unresolved questions with the user, then set open_questions_reviewed to true.")

    local_citations: list[dict[str, str]] = []
    path_errors: list[dict[str, str]] = []
    if not paths_are_list:
        path_errors.append({"path": "", "reason": "Related paths must be supplied as a list."})
    elif len(paths) > MAX_RELATED_PATHS:
        path_errors.append({"path": "", "reason": f"At most {MAX_RELATED_PATHS} related paths may be supplied."})
    elif paths and read_document:
        for raw_path in paths:
            path = _local_path(raw_path)
            if path is None:
                path_errors.append({"path": _text(raw_path), "reason": "Path must be project-relative and cannot contain traversal or backslashes."})
                continue
            try:
                document = read_document(clean_project, path)
            except (ValueError, OSError) as exc:
                path_errors.append({"path": path, "reason": str(exc)})
                continue
            local_citations.append({
                "project": clean_project,
                "path": str(document["path"]),
                "uri": str(document["uri"]),
                "title": str(document["title"]),
                "content_hash": str(document["content_hash"]),
            })
    elif paths:
        path_errors.append({"path": "", "reason": "Local source validation is not configured."})
    local_citations.sort(key=lambda item: (item["project"], item["path"]))
    check("related_sources", not path_errors,
          "Supplied related documents are allowlisted and readable." if paths and not path_errors else
          ("No related documents were supplied." if not paths else "One or more related documents could not be validated."),
          "Correct or remove the related paths that failed validation.")

    external_citations: list[dict[str, str]] = []
    url_errors: list[dict[str, str]] = []
    if not urls_are_list:
        url_errors.append({"url": "", "reason": "External sources must be supplied as a list."})
    elif len(urls) > MAX_EXTERNAL_SOURCES:
        url_errors.append({"url": "", "reason": f"At most {MAX_EXTERNAL_SOURCES} external sources may be supplied."})
    else:
        for raw_url in urls:
            citation = _external_source(raw_url)
            if citation is None:
                url_errors.append({"url": _text(raw_url), "reason": "Use a valid HTTP or HTTPS URL without embedded credentials."})
            else:
                external_citations.append(citation)
    external_citations.sort(key=lambda item: item["url"])
    check("external_sources", not url_errors,
          "Supplied external URLs passed syntax validation; no network fetch was made." if urls and not url_errors else
          ("No external URLs were supplied." if not urls else "One or more external URLs are invalid."),
          "Correct or remove the external URLs that failed validation.")

    canonical = {
        "project": clean_project,
        "title": clean_title,
        "memo_kind": clean_kind,
        "draft": clean_draft,
        "purpose": clean_purpose,
        "scope": clean_scope,
        "next_actions": actions,
        "open_questions_reviewed": questions_ok,
        "local_citations": local_citations,
        "external_citations": external_citations,
        "related_paths_supplied": sorted(_text(item) for item in paths),
        "external_sources_supplied": sorted(_text(item) for item in urls),
    }
    canonical_bytes = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    ready = all(item["status"] == "passed" for item in checks)
    return {
        "status": "ready_for_user_approval" if ready else "needs_refinement",
        "approval_required": True,
        "checklist": checks,
        "refinement_questions": list(dict.fromkeys(questions)),
        "sources": {
            "local": local_citations,
            "local_errors": path_errors,
            "external": external_citations,
            "external_errors": url_errors,
        },
        "review_signature": {
            "algorithm": "sha256",
            "digest": digest,
            "canonicalization": _CANONICALIZATION,
            "ready_for_user_approval": ready,
        },
        "draft_persisted": False,
    }
