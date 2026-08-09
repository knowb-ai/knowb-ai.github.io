"""Operator CLI for discovery, indexing, local inspection, and stdio serving."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

from .config import ConfigurationError
from .design_assets import DesignAssetError
from .env import EnvironmentFileError
from .github_ops import GitHubError
from .index import IndexError
from .service import OrgIndexService


def _json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knowb-org",
        description="Operate the local-first KnowB organization index",
    )
    parser.add_argument("--config", type=Path, help="Local registry YAML path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show registered projects and local candidates")
    sub.add_parser("discover", help="Discover KnowB candidates within allowed roots")
    sub.add_parser("doctor", help="Check runtime, paths, and project availability")

    index = sub.add_parser("index", help="Incrementally index local project knowledge")
    index.add_argument("projects", nargs="*", help="Project ids; all when omitted")

    search = sub.add_parser("search", help="Search local project knowledge")
    search.add_argument("query")
    search.add_argument("--project", action="append", dest="projects")
    search.add_argument("--tag", action="append", dest="tags")
    search.add_argument("--limit", type=int, default=10)

    read = sub.add_parser("read", help="Read one indexed/allowlisted document")
    read.add_argument("project")
    read.add_argument("path")

    context = sub.add_parser("context", help="Show a project's full local context map")
    context.add_argument("project")

    manifest = sub.add_parser("manifest", help="Print the repo-owned manifest template")
    manifest.add_argument("project")

    work = sub.add_parser("work", help="List organization GitHub issues")
    work.add_argument("--repo")
    work.add_argument("--state", default="open", choices=["open", "closed", "all"])
    work.add_argument("--label")
    work.add_argument("--assignee")
    work.add_argument("--query")
    work.add_argument("--limit", type=int, default=50)

    ticket = sub.add_parser("ticket", help="Read one GitHub issue")
    ticket.add_argument("repository")
    ticket.add_argument("number", type=int)

    project = sub.add_parser("github-project", help="Read one organization GitHub Project")
    project.add_argument("number", type=int)
    project.add_argument("--no-items", action="store_true")

    sub.add_parser(
        "design-assets-verify",
        help="Verify the private Google Drive design-asset vault and identities",
    )
    sub.add_parser(
        "design-assets-auth",
        help="Approve Google Drive access in the browser and store the grant in Keychain",
    )
    assets = sub.add_parser("design-assets-list", help="List private Google Drive design assets")
    assets.add_argument("--limit", type=int, default=100)
    read_asset = sub.add_parser("design-assets-read", help="Read one private design asset")
    read_asset.add_argument("file_id")
    upload = sub.add_parser(
        "design-assets-propose-upload", help="Propose a private design-asset upload"
    )
    upload.add_argument("local_path")
    upload.add_argument("--name", dest="display_name")
    upload.add_argument("--idempotency-key")
    confirm_upload = sub.add_parser(
        "design-assets-confirm-upload", help="Confirm a proposed design-asset upload"
    )
    confirm_upload.add_argument("token")

    sub.add_parser("serve", help="Run the MCP server over local stdio")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        service = OrgIndexService(args.config)
        if args.command == "status":
            _json(service.list_projects(include_candidates=True))
        elif args.command == "discover":
            _json(service.discover_local_repos())
        elif args.command == "doctor":
            directory = service.list_projects(include_candidates=True)
            _json(
                {
                    "ok": True,
                    "config": str(service.registry.config_path),
                    "database": str(service.registry.database_path),
                    "git": shutil.which("git"),
                    "gh": shutil.which("gh"),
                    "registered": directory["summary"],
                    "warnings": [
                        {"project": project.id, "warnings": list(project.warnings)}
                        for project in service.registry.projects
                        if project.warnings
                    ],
                }
            )
        elif args.command == "index":
            _json(service.refresh_index(args.projects or None))
        elif args.command == "search":
            _json(
                service.search_knowledge(
                    args.query,
                    projects=args.projects,
                    tags=args.tags,
                    limit=args.limit,
                )
            )
        elif args.command == "read":
            _json(service.read_project_doc(args.project, args.path))
        elif args.command == "context":
            _json(service.get_project_context(args.project))
        elif args.command == "manifest":
            print(service.project_manifest_template(args.project), end="")
        elif args.command == "work":
            _json(
                service.github.list_work(
                    repository=args.repo,
                    state=args.state,
                    label=args.label,
                    assignee=args.assignee,
                    query=args.query,
                    limit=args.limit,
                )
            )
        elif args.command == "ticket":
            _json(service.github.get_ticket(args.repository, args.number))
        elif args.command == "github-project":
            _json(service.github.get_project(args.number, include_items=not args.no_items))
        elif args.command == "design-assets-verify":
            _json(service.design_assets.verify())
        elif args.command == "design-assets-auth":
            _json(service.design_assets.authenticate())
        elif args.command == "design-assets-list":
            _json(service.design_assets.list_assets(limit=args.limit))
        elif args.command == "design-assets-read":
            _json(service.design_assets.read_asset(args.file_id))
        elif args.command == "design-assets-propose-upload":
            _json(
                service.design_assets.propose_upload(
                    local_path=args.local_path,
                    display_name=args.display_name,
                    idempotency_key=args.idempotency_key,
                )
            )
        elif args.command == "design-assets-confirm-upload":
            _json(service.design_assets.confirm(args.token))
        elif args.command == "serve":
            from .server import create_server

            create_server(args.config).run()
        else:
            raise ConfigurationError(f"Unknown command: {args.command}")
        return 0
    except (
        ConfigurationError,
        DesignAssetError,
        EnvironmentFileError,
        GitHubError,
        IndexError,
        OSError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
