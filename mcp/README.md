# KnowB Org Index MCP

Local-first directory, knowledge index, and GitHub work control plane for the
`knowb-ai` organization. It runs beside the Zola site; it does not alter or
serve the website.

## Guarantees

- Project knowledge is read only from explicitly registered local clones.
- Discovery is bounded to `allowed_roots`; it never scans the whole computer.
- Discovered repositories are candidates only and are not automatically indexed.
- Resolved files must stay inside their project root; symlinks are not followed.
- Brandbook/Org Book sources remain public on the website but are denied from the
  private MCP knowledge index.
- The MCP transport is local stdio by default and opens no listening port.
- GitHub is contacted only by explicit ticket/project/repository tools.
- GitHub writes require a durable proposal, a short-lived confirmation token,
  idempotency protection, and a local audit record.

The local server cannot guarantee that returned content stays on-device when its
client uses a hosted model. For strict no-egress use, connect it to a local model
and client. This is a client boundary, not a server configuration switch.

## Runtime

- Python 3.11+
- `uv`
- GitHub CLI (`gh`) and Git for ticket/project/repository operations
- MCP Python SDK 2.x

The implementation follows the current MCP Python SDK v2 surface: `MCPServer`
with local stdio as the default transport.

## Start locally

From the repository root:

~~~sh
uv sync --project mcp
uv run --project mcp knowb-org doctor
uv run --project mcp knowb-org index
uv run --project mcp knowb-org search "knowledge agent"
~~~

The default loader uses `config/local-projects.yml` when present, otherwise
`config/local-projects.example.yml`. Override it with either `--config` or:

~~~sh
export KNOWB_ORG_CONFIG=/absolute/path/to/local-projects.yml
~~~

Local state is stored in `.knowb-state/org-index.sqlite` and ignored by git.
The SQLite database is a disposable cache and audit ledger; project files remain
the knowledge source of truth.

## Connect an MCP client

Use the shape in `config/mcp-client.example.json`, replacing the repository path
with its absolute local path. The launch command is:

~~~sh
uv run --project /absolute/path/to/knowb-ai.github.io/mcp knowb-org-mcp
~~~

No HTTP endpoint is created. The MCP host launches this process and communicates
over stdin/stdout.

## Knowledge tools

- `list_projects` — registered projects and optional local candidates
- `discover_local_repos` — bounded inventory of all local organization clones
- `refresh_index` — incremental changed-file refresh
- `search_knowledge` — local FTS search with exact source paths and `knowb://` URIs
- `read_project_doc` — safe allowlisted document retrieval
- `get_project_context` — project map, decisions, documents, ticket references
- `find_related_work` — ticket/query-to-local-knowledge lookup

Directory resources:

- `knowb://org/overview`
- `knowb://project/{project_id}`

## GitHub tools

Read operations:

- `list_work`
- `get_ticket`
- `get_github_project`

Mutations are intentionally two-step:

1. Call `propose_ticket_create`, `propose_ticket_update`, or
   `propose_project_update`.
2. Review the returned preview.
3. Call the matching `confirm_*` tool with its token.

Confirmation tokens expire, are single-purpose, and return the cached result if
a completed token is replayed. `audit_log` reports proposals, completions,
failures, and expirations. Ticket and project mutations never read local project
documents.

## Create a new KnowB repository

Repository creation is a guided, four-tool workflow. It supports both public and
private repositories, but it will not create a generic empty repo or silently invent
the product direction.

1. Invoke the MCP prompt `/remix`, which drives the MCP tool named `remix` with what is
   already known. The tool returns
   Socratic questions until the project's purpose, audience, personality, desired
   feeling, visual metaphor, content priority, interface place, and proof surfaces are
   explicit. Review its narrative, visual system, six-panel gallery direction, and
   `remix_digest`.
2. Call `draft_repository_blueprint` with what is already known plus the reviewed
   `design_remix` brief and `remix_digest`. It returns focused
   questions until purpose, audience, primary users, 6-12 month direction, success
   criteria, brand tone, and stack are complete.
3. Review the rendered brand narrative, strategic direction, visual design system,
   visibility, license, and `public-facing`, `internal`, or scoped `hybrid` mode.
4. Call `propose_repository_create` with the unchanged completed brief and its
   `blueprint_digest`; review the exact target and file list.
5. Call `confirm_repository_create` with the proposal token.

### `/remix` contract

The remix follows the existing two-place KnowB visual system:

- **KnowB Autumn** owns public organization, ecosystem narrative, editorial, campaign,
  and collateral surfaces.
- **Kenobi Digital Surface** owns authenticated runtime, dashboard, workflow, library,
  and product interaction surfaces: high-signal gold/yellow over indigo-midnight-purple
  depth.
- **Hybrid** projects may use both, but each surface stays in its correct place. The
  palettes are not blended into a third theme.

Project identity is created by remixing narrative, metaphor, composition, density,
type emphasis, imagery, and content hierarchy while retaining canonical hue roles,
copy rules, explicit product state, and WCAG 2.2 AA requirements. The result includes:

- a project-specific brand narrative and strategic direction;
- semantic tokens and component rules for the selected place or scoped hybrid;
- provenance back to the KnowB system documents and local Kenobi precedent;
- a deterministic digest required by repository creation;
- six proof surfaces and one image-generation prompt for a single 3x2 carousel/contact
  sheet containing a landing page, library/dashboard, detail/evidence view, mobile flow,
  campaign asset, and token/component specimen (or six user-selected surfaces).

The `/remix` prompt tells an image-capable MCP host to execute the returned
`harness_action` after the user accepts the remix and display the one generated image
inline. The MCP server itself does not contact an image service or send local project
documents over the network.

Confirmation creates a new directory beneath a configured `allowed_root`, initializes
`main`, commits the scaffold, creates `knowb-ai/<name>`, and pushes it. Existing paths
are never overwritten. The generated baseline contains:

~~~text
README.md
.gitignore
LICENSE
CONTRIBUTING.md
AGENTS.md
.knowb/project.yml
docs/
├── README.md
├── brand-narrative-and-strategic-direction.md
├── visual-design-system.md
├── architecture/README.md
├── decisions/README.md
├── decisions/0000-decision-template.md
├── research/README.md
└── operations/README.md
~~~

The visual document contains the accepted `/remix` result: compact semantic tokens,
baseline components, narrative, metaphor, and composition rules adapted to public,
internal, or explicitly scoped hybrid use. The
project manifest makes the new repo a candidate for local discovery immediately; add
it to `config/local-projects.yml` when it should be indexed.

If GitHub creation or push fails after local initialization, the local repository is
kept for diagnosis and recovery, and the failed confirmation is recorded in the audit
log. The tool does not delete or overwrite work to simulate a rollback.

## Adopt a project-owned knowledge wiki

Each project should add `.knowb/project.yml` and a `docs/` wiki:

~~~text
project/
├── .knowb/
│   └── project.yml
└── docs/
    ├── README.md
    ├── brand-narrative-and-strategic-direction.md
    ├── visual-design-system.md
    ├── architecture/
    ├── decisions/
    ├── research/
    └── operations/
~~~

Generate the correct manifest for a registered project without writing to it:

~~~sh
uv run --project mcp knowb-org manifest BetterHackdays
~~~

The manifest schema is `config/project.schema.json`. During migration,
`strict_manifests: false` permits an explicit registry knowledge policy. Set it
to `true` once every active repo owns its manifest.

## Operator commands

~~~text
knowb-org status
knowb-org discover
knowb-org doctor
knowb-org index [PROJECT ...]
knowb-org search QUERY [--project PROJECT]
knowb-org read PROJECT PATH
knowb-org context PROJECT
knowb-org manifest PROJECT
knowb-org work [--repo knowb-ai/REPO]
knowb-org ticket knowb-ai/REPO NUMBER
knowb-org github-project NUMBER
knowb-org serve
~~~

`scripts/discover-local-repos` is a convenience wrapper around the bounded
discovery command.
