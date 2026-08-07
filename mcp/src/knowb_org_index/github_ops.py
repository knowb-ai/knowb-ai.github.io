"""Explicit GitHub issue/project reads and confirmed mutation execution."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any

from .index import LocalIndex


_REPO = re.compile(r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<name>[A-Za-z0-9_.-]+)$")


class GitHubError(RuntimeError):
    """Raised when a validated GitHub CLI operation fails."""


class GitHubOperations:
    """GitHub boundary. No method reads or uploads local project documents."""

    def __init__(self, organization: str, index: LocalIndex) -> None:
        self.organization = organization
        self.index = index

    def _repo(self, repository: str) -> str:
        match = _REPO.fullmatch(repository.strip())
        if not match or match.group("owner").casefold() != self.organization.casefold():
            raise GitHubError(
                f"Repository must be inside {self.organization} and formatted owner/name"
            )
        return repository

    @staticmethod
    def _project_number(value: int) -> int:
        number = int(value)
        if number < 1:
            raise GitHubError("GitHub project number must be positive")
        return number

    @staticmethod
    def _run(
        args: list[str],
        *,
        expect_json: bool = False,
        input_text: str | None = None,
    ) -> Any:
        if shutil.which("gh") is None:
            raise GitHubError("GitHub CLI (gh) is required for ticket/project operations")
        try:
            result = subprocess.run(
                ["gh", *args],
                input=input_text,
                check=False,
                capture_output=True,
                text=True,
                timeout=45,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitHubError("GitHub operation timed out") from exc
        except OSError as exc:
            raise GitHubError(f"Cannot execute GitHub CLI: {exc}") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise GitHubError(detail[:1500] or f"gh exited with status {result.returncode}")
        output = result.stdout.strip()
        if not expect_json:
            return output
        if not output:
            return {}
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise GitHubError("GitHub CLI returned invalid JSON") from exc

    def list_work(
        self,
        *,
        repository: str | None = None,
        state: str = "open",
        label: str | None = None,
        assignee: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        if state not in {"open", "closed", "all"}:
            raise GitHubError("state must be open, closed, or all")
        terms = [f"org:{self.organization}", "is:issue"]
        if repository:
            terms.append(f"repo:{self._repo(repository)}")
        if state != "all":
            terms.append(f"state:{state}")
        if label:
            terms.append(f'label:"{label}"')
        if assignee:
            terms.append(f"assignee:{assignee}")
        if query:
            terms.append(query.strip())
        capped = max(1, min(int(limit), 100))
        response = self._run(
            [
                "api",
                "--method",
                "GET",
                "search/issues",
                "-f",
                f"q={' '.join(terms)}",
                "-f",
                f"per_page={capped}",
            ],
            expect_json=True,
        )
        items = response.get("items", []) if isinstance(response, dict) else []
        return {
            "query": " ".join(terms),
            "total_count": response.get("total_count", len(items)),
            "items": [
                {
                    "repository": "/".join(item.get("repository_url", "").split("/")[-2:]),
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "url": item.get("html_url"),
                    "labels": [label_item.get("name") for label_item in item.get("labels", [])],
                    "assignees": [user.get("login") for user in item.get("assignees", [])],
                    "updated_at": item.get("updated_at"),
                }
                for item in items
            ],
        }

    def get_ticket(self, repository: str, number: int) -> dict[str, Any]:
        repo = self._repo(repository)
        issue_number = int(number)
        if issue_number < 1:
            raise GitHubError("Issue number must be positive")
        item = self._run(
            ["api", f"repos/{repo}/issues/{issue_number}"], expect_json=True
        )
        return {
            "repository": repo,
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "body": item.get("body"),
            "url": item.get("html_url"),
            "labels": [label.get("name") for label in item.get("labels", [])],
            "assignees": [user.get("login") for user in item.get("assignees", [])],
            "milestone": (item.get("milestone") or {}).get("title"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }

    def get_project(self, project_number: int, *, include_items: bool = True) -> dict[str, Any]:
        number = self._project_number(project_number)
        project = self._run(
            [
                "project",
                "view",
                str(number),
                "--owner",
                self.organization,
                "--format",
                "json",
            ],
            expect_json=True,
        )
        if include_items:
            project["items"] = self._run(
                [
                    "project",
                    "item-list",
                    str(number),
                    "--owner",
                    self.organization,
                    "--limit",
                    "100",
                    "--format",
                    "json",
                ],
                expect_json=True,
            ).get("items", [])
        return project

    def propose_ticket_create(
        self,
        *,
        repository: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        project_number: int | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        repo = self._repo(repository)
        clean_title = title.strip()
        if not clean_title:
            raise GitHubError("Ticket title cannot be empty")
        if len(clean_title) > 256:
            raise GitHubError("Ticket title cannot exceed 256 characters")
        if len(body) > 65_536:
            raise GitHubError("Ticket body cannot exceed 65,536 characters")
        payload = {
            "repository": repo,
            "title": clean_title,
            "body": body,
            "labels": [item for item in (labels or []) if item],
            "assignees": [item for item in (assignees or []) if item],
            "project_number": self._project_number(project_number) if project_number else None,
        }
        preview = {
            "operation": "create GitHub issue",
            "target": repo,
            "title": clean_title,
            "labels": payload["labels"],
            "assignees": payload["assignees"],
            "project_number": payload["project_number"],
            "body_preview": body[:500],
            "requires_confirmation": True,
        }
        return self.index.create_pending_action(
            kind="ticket_create",
            payload=payload,
            preview=preview,
            idempotency_key=idempotency_key,
        )

    def propose_ticket_update(
        self,
        *,
        repository: str,
        number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
        add_assignees: list[str] | None = None,
        remove_assignees: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        repo = self._repo(repository)
        issue_number = int(number)
        if issue_number < 1:
            raise GitHubError("Issue number must be positive")
        if state is not None and state not in {"open", "closed"}:
            raise GitHubError("state must be open or closed")
        if title is not None and (not title.strip() or len(title) > 256):
            raise GitHubError("Ticket title must be 1-256 characters when provided")
        if body is not None and len(body) > 65_536:
            raise GitHubError("Ticket body cannot exceed 65,536 characters")
        payload = {
            "repository": repo,
            "number": issue_number,
            "title": title,
            "body": body,
            "state": state,
            "add_labels": [item for item in (add_labels or []) if item],
            "remove_labels": [item for item in (remove_labels or []) if item],
            "add_assignees": [item for item in (add_assignees or []) if item],
            "remove_assignees": [item for item in (remove_assignees or []) if item],
        }
        changes = {key: value for key, value in payload.items() if key not in {"repository", "number"} and value not in (None, [], "")}
        if not changes:
            raise GitHubError("Ticket update contains no changes")
        preview = {
            "operation": "update GitHub issue",
            "target": f"{repo}#{issue_number}",
            "changes": changes,
            "requires_confirmation": True,
        }
        return self.index.create_pending_action(
            kind="ticket_update",
            payload=payload,
            preview=preview,
            idempotency_key=idempotency_key,
        )

    def propose_project_update(
        self,
        *,
        project_number: int,
        item_id: str,
        field_id: str,
        value_type: str,
        value: str | float | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        number = self._project_number(project_number)
        allowed_types = {"text", "number", "date", "single_select", "iteration", "clear"}
        if value_type not in allowed_types:
            raise GitHubError(f"value_type must be one of {sorted(allowed_types)}")
        if value_type != "clear" and value is None:
            raise GitHubError("value is required unless value_type is clear")
        if not item_id.strip() or not field_id.strip():
            raise GitHubError("item_id and field_id are required")
        payload = {
            "project_number": number,
            "item_id": item_id.strip(),
            "field_id": field_id.strip(),
            "value_type": value_type,
            "value": value,
        }
        preview = {
            "operation": "update GitHub Project field",
            "target": f"{self.organization} project {number}, item {item_id}",
            "field_id": field_id,
            "value_type": value_type,
            "value": value,
            "requires_confirmation": True,
        }
        return self.index.create_pending_action(
            kind="project_update",
            payload=payload,
            preview=preview,
            idempotency_key=idempotency_key,
        )

    def confirm(self, token: str) -> dict[str, Any]:
        pending, claimed = self.index.claim_pending_action(token)
        if pending is None:
            raise GitHubError("Unknown confirmation token")
        if pending["status"] == "completed":
            return {
                "status": "completed",
                "idempotent_replay": True,
                "result": pending["result"],
            }
        if pending["expired"] and pending["status"] == "pending":
            result = {"error": "Confirmation token expired"}
            audit_id = self.index.finish_pending_action(token, status="expired", result=result)
            raise GitHubError(f"Confirmation token expired (audit {audit_id})")
        if not claimed:
            raise GitHubError(f"Action cannot be confirmed from status {pending['status']}")

        try:
            result = self._execute(pending["kind"], pending["payload"])
        except Exception as exc:
            failure = {"error": str(exc)}
            audit_id = self.index.finish_pending_action(token, status="failed", result=failure)
            raise GitHubError(f"Confirmed action failed (audit {audit_id}): {exc}") from exc
        audit_id = self.index.finish_pending_action(token, status="completed", result=result)
        return {"status": "completed", "audit_id": audit_id, "result": result}

    def _execute(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if kind == "ticket_create":
            return self._execute_ticket_create(payload)
        if kind == "ticket_update":
            return self._execute_ticket_update(payload)
        if kind == "project_update":
            return self._execute_project_update(payload)
        raise GitHubError(f"Unsupported action kind: {kind}")

    def _execute_ticket_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = [
            "issue",
            "create",
            "--repo",
            payload["repository"],
            "--title",
            payload["title"],
            "--body-file",
            "-",
        ]
        for label in payload.get("labels", []):
            args.extend(["--label", label])
        for assignee in payload.get("assignees", []):
            args.extend(["--assignee", assignee])
        issue_url = self._run(args, input_text=payload.get("body", ""))
        result: dict[str, Any] = {"url": issue_url, "repository": payload["repository"]}
        project_number = payload.get("project_number")
        if project_number:
            result["project_item"] = self._run(
                [
                    "project",
                    "item-add",
                    str(project_number),
                    "--owner",
                    self.organization,
                    "--url",
                    issue_url,
                    "--format",
                    "json",
                ],
                expect_json=True,
            )
        return result

    def _execute_ticket_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        repo = payload["repository"]
        number = str(payload["number"])
        args = ["issue", "edit", number, "--repo", repo]
        body_input: str | None = None
        if payload.get("title") is not None:
            args.extend(["--title", payload["title"]])
        if payload.get("body") is not None:
            args.extend(["--body-file", "-"])
            body_input = payload["body"]
        for label in payload.get("add_labels", []):
            args.extend(["--add-label", label])
        for label in payload.get("remove_labels", []):
            args.extend(["--remove-label", label])
        for assignee in payload.get("add_assignees", []):
            args.extend(["--add-assignee", assignee])
        for assignee in payload.get("remove_assignees", []):
            args.extend(["--remove-assignee", assignee])
        if len(args) > 5:
            self._run(args, input_text=body_input)
        state = payload.get("state")
        if state == "closed":
            self._run(["issue", "close", number, "--repo", repo])
        elif state == "open":
            self._run(["issue", "reopen", number, "--repo", repo])
        return self.get_ticket(repo, int(number))

    def _execute_project_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        project = self.get_project(payload["project_number"], include_items=False)
        project_id = project.get("id")
        if not project_id:
            raise GitHubError("GitHub Project response did not include a project id")
        args = [
            "project",
            "item-edit",
            "--id",
            payload["item_id"],
            "--project-id",
            project_id,
            "--field-id",
            payload["field_id"],
        ]
        value_type = payload["value_type"]
        flags = {
            "text": "--text",
            "number": "--number",
            "date": "--date",
            "single_select": "--single-select-option-id",
            "iteration": "--iteration-id",
        }
        if value_type == "clear":
            args.append("--clear")
        else:
            args.extend([flags[value_type], str(payload["value"])])
        self._run(args)
        return {
            "project_number": payload["project_number"],
            "project_id": project_id,
            "item_id": payload["item_id"],
            "field_id": payload["field_id"],
            "value_type": value_type,
            "value": payload.get("value"),
        }
