"""MCP v2 stdio server for the KnowB local organization control plane."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from . import __version__
from .service import OrgIndexService


def create_server(config_path: str | Path | None = None) -> MCPServer:
    service = OrgIndexService(config_path)
    server = MCPServer(
        "KnowB Org Index",
        version=__version__,
        instructions=(
            "Local-first directory for KnowB AI projects. Knowledge tools read only from "
            "explicitly registered local clones. GitHub writes always use a proposal followed "
            "by a confirmation token. Run remix as a Socratic loop before creating a repository; "
            "when its result is ready, an image-capable host should execute harness_action and "
            "show the single six-panel gallery image to the user. Never assume tool content "
            "stays on-device when the MCP client uses a hosted model."
        ),
    )

    @server.tool()
    def list_projects(include_candidates: bool = True) -> dict[str, Any]:
        """List registered projects and optional unregistered local KnowB candidates."""

        return service.list_projects(include_candidates=include_candidates)

    @server.tool()
    def discover_local_repos() -> dict[str, Any]:
        """Discover every local knowb-ai clone inside configured roots, without indexing it."""

        return service.discover_local_repos()

    @server.tool()
    def refresh_index(projects: list[str] | None = None) -> dict[str, Any]:
        """Incrementally refresh local knowledge for selected or all registered projects."""

        return service.refresh_index(projects)

    @server.tool()
    def search_knowledge(
        query: str,
        projects: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search allowlisted local project knowledge and return exact source citations."""

        return service.search_knowledge(query, projects=projects, tags=tags, limit=limit)

    @server.tool()
    def read_project_doc(project: str, path: str) -> dict[str, Any]:
        """Read one document only when it belongs to that project's indexed allowlist."""

        return service.read_project_doc(project, path)

    @server.tool()
    def get_project_context(project: str) -> dict[str, Any]:
        """Return the project directory entry, document map, decisions, and ticket references."""

        return service.get_project_context(project)

    @server.tool()
    def find_related_work(
        project: str,
        ticket: int | None = None,
        query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Find local knowledge related to a ticket number or arbitrary work query."""

        return service.find_related_work(
            project=project, ticket=ticket, query=query, limit=limit
        )

    @server.tool()
    def list_work(
        repository: str | None = None,
        state: str = "open",
        label: str | None = None,
        assignee: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List GitHub issues across knowb-ai without reading repository documents."""

        return service.github.list_work(
            repository=repository,
            state=state,
            label=label,
            assignee=assignee,
            query=query,
            limit=limit,
        )

    @server.tool()
    def get_ticket(repository: str, number: int) -> dict[str, Any]:
        """Read one GitHub issue from a knowb-ai repository."""

        return service.github.get_ticket(repository, number)

    @server.tool()
    def get_github_project(project_number: int, include_items: bool = True) -> dict[str, Any]:
        """Read an organization GitHub Project and optionally its first 100 items."""

        return service.github.get_project(project_number, include_items=include_items)

    @server.tool()
    def remix(
        project_name: str,
        purpose: str = "",
        audience: str = "",
        personality: str = "",
        desired_feeling: str = "",
        visual_metaphor: str = "",
        content_priority: str = "",
        interface_mode: str = "",
        density: str = "balanced",
        surfaces: list[str] | None = None,
        avoid: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run /remix: a Socratic, two-place brand and six-panel gallery design loop."""

        return service.remix(
            project_name=project_name,
            purpose=purpose,
            audience=audience,
            personality=personality,
            desired_feeling=desired_feeling,
            visual_metaphor=visual_metaphor,
            content_priority=content_priority,
            interface_mode=interface_mode,
            density=density,
            surfaces=surfaces,
            avoid=avoid,
        )

    @server.tool()
    def draft_repository_blueprint(
        name: str,
        purpose: str = "",
        audience: str = "",
        primary_users: str = "",
        strategic_direction: str = "",
        success_criteria: str = "",
        brand_tone: str = "",
        visibility: str = "private",
        interface_mode: str = "internal",
        tech_stack: list[str] | None = None,
        license_name: str = "MIT",
        design_remix: dict[str, Any] | None = None,
        remix_digest: str = "",
    ) -> dict[str, Any]:
        """Ideate a new repository; returns questions until the required brief is complete."""

        return service.draft_repository_blueprint(
            name=name,
            purpose=purpose,
            audience=audience,
            primary_users=primary_users,
            strategic_direction=strategic_direction,
            success_criteria=success_criteria,
            brand_tone=brand_tone,
            visibility=visibility,
            interface_mode=interface_mode,
            tech_stack=tech_stack,
            license_name=license_name,
            design_remix=design_remix,
            remix_digest=remix_digest,
        )

    @server.tool()
    def propose_repository_create(
        name: str,
        purpose: str,
        audience: str,
        primary_users: str,
        strategic_direction: str,
        success_criteria: str,
        brand_tone: str,
        blueprint_digest: str,
        visibility: str = "private",
        interface_mode: str = "internal",
        tech_stack: list[str] | None = None,
        license_name: str = "MIT",
        design_remix: dict[str, Any] | None = None,
        remix_digest: str = "",
        local_parent: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Preview a reviewed repo bootstrap; no local or GitHub writes occur yet."""

        return service.github.propose_repository_create(
            name=name,
            purpose=purpose,
            audience=audience,
            primary_users=primary_users,
            strategic_direction=strategic_direction,
            success_criteria=success_criteria,
            brand_tone=brand_tone,
            blueprint_digest=blueprint_digest,
            visibility=visibility,
            interface_mode=interface_mode,
            tech_stack=tech_stack,
            license_name=license_name,
            design_remix=design_remix,
            remix_digest=remix_digest,
            local_parent=local_parent,
            idempotency_key=idempotency_key,
        )

    @server.tool()
    def confirm_repository_create(token: str) -> dict[str, Any]:
        """Create, initialize, commit, and push a reviewed repository exactly once."""

        return _confirm_kind(service, token, "repository_create")

    @server.tool()
    def propose_ticket_create(
        repository: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        project_number: int | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Preview and persist a ticket creation; this does not write to GitHub."""

        return service.github.propose_ticket_create(
            repository=repository,
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            project_number=project_number,
            idempotency_key=idempotency_key,
        )

    @server.tool()
    def confirm_ticket_create(token: str) -> dict[str, Any]:
        """Execute a previously previewed ticket creation exactly once."""

        return _confirm_kind(service, token, "ticket_create")

    @server.tool()
    def propose_ticket_update(
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
        """Preview and persist a ticket update; this does not write to GitHub."""

        return service.github.propose_ticket_update(
            repository=repository,
            number=number,
            title=title,
            body=body,
            state=state,
            add_labels=add_labels,
            remove_labels=remove_labels,
            add_assignees=add_assignees,
            remove_assignees=remove_assignees,
            idempotency_key=idempotency_key,
        )

    @server.tool()
    def confirm_ticket_update(token: str) -> dict[str, Any]:
        """Execute a previously previewed ticket update exactly once."""

        return _confirm_kind(service, token, "ticket_update")

    @server.tool()
    def propose_project_update(
        project_number: int,
        item_id: str,
        field_id: str,
        value_type: str,
        value: str | float | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Preview a GitHub Projects v2 field update without executing it."""

        return service.github.propose_project_update(
            project_number=project_number,
            item_id=item_id,
            field_id=field_id,
            value_type=value_type,
            value=value,
            idempotency_key=idempotency_key,
        )

    @server.tool()
    def confirm_project_update(token: str) -> dict[str, Any]:
        """Execute a previously previewed GitHub Projects field update exactly once."""

        return _confirm_kind(service, token, "project_update")

    @server.tool()
    def audit_log(limit: int = 50) -> dict[str, Any]:
        """Read the local audit log for proposed, completed, failed, or expired mutations."""

        return {"events": service.index.audit_log(limit)}

    @server.resource("knowb://org/overview")
    def org_overview() -> str:
        """Human/agent-readable organization directory and privacy boundary."""

        return json.dumps(service.org_overview(), indent=2, sort_keys=True)

    @server.resource("knowb://project/{project_id}")
    def project_resource(project_id: str) -> str:
        """Directory and knowledge map for one registered project."""

        return json.dumps(service.get_project_context(project_id), indent=2, sort_keys=True)

    @server.prompt()
    def plan_project_work(project: str, objective: str) -> str:
        """Guide an agent to plan work from local context and GitHub state."""

        return (
            f"Plan work for KnowB project {project!r} toward {objective!r}. "
            "First call get_project_context, then list_work for its GitHub repository, "
            "then search_knowledge for the objective. Cite local document paths. "
            "Do not mutate GitHub until a proposal preview has been shown and its token "
            "is explicitly confirmed."
        )

    @server.prompt(name="remix")
    def remix_prompt(project_name: str, known_context: str = "") -> str:
        """Run the complete Socratic remix and visual proof workflow."""

        return (
            f"Run the KnowB /remix workflow for {project_name!r}. Known context: "
            f"{known_context or 'none supplied'}. Call the remix tool with known answers, ask "
            "the user its returned questions without inventing project direction, and call remix "
            "again until ready. Review the two-place selection, narrative, tokens, components, "
            "six panels, compliance report, and digest with the user. Then execute the returned "
            "harness_action using the host's image-generation capability and display exactly one "
            "six-panel landscape gallery image inline. If creating a repository, pass the accepted "
            "brief and remix_digest unchanged into draft_repository_blueprint."
        )

    return server


def _confirm_kind(service: OrgIndexService, token: str, expected: str) -> dict[str, Any]:
    pending = service.index.get_pending_action(token)
    if pending is None:
        raise ValueError("Unknown confirmation token")
    if pending["kind"] != expected:
        raise ValueError(f"Confirmation token is for {pending['kind']}, not {expected}")
    return service.github.confirm(token)


def main() -> None:
    """Run the local server over stdio (the MCP SDK default transport)."""

    create_server().run()


if __name__ == "__main__":
    main()
