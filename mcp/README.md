# KnowB Org Index MCP

Local-first directory, knowledge index, and GitHub work control plane for the
`knowb-ai` organization. It runs beside the Zola site; it does not alter or
serve the website.

Portable installation and folder onboarding are scoped in the
[packaging implementation and test plan](docs/portable-packaging-plan.md) and the
[core implementation plan](docs/portable-connector-core-implementation-plan.md).
The release and knowledgeHQ migration procedure is in the
[P6 release plan](docs/portable-release-migration-plan.md).
This branch packages the native `okf-rs` adapter and keeps source-checkout launch
available as verified legacy mode while the release and knowledgeHQ migration are
completed under issue #9.

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
- Private design assets are a separate, disabled-by-default capability. Every
  Drive read requires an allowlisted GitHub login, an allowlisted verified Google
  account, and a folder/file ACL with no public, domain, or group permission.
- Design-asset uploads are restricted to configured local roots and require the
  same proposal/confirmation/audit flow as other external writes.

## New repository contract

The reviewed repository-creation flow initializes every new repository with a
`.knowb/project.yml` passport, a `.knowb/mcp-client.example.json` client template,
MCP-first `AGENTS.md` instructions, and
`docs/operations/knowb-mcp-validation.md`. The generated instructions tell agents
to retrieve approved KnowledgeHQ decisions, boundaries, constraints, and direction
before running the repository's native checks.

The passport makes a repository connector-ready and a candidate for discovery. An
owner or operator must still explicitly add and enable its local clone in the private
KnowledgeHQ registry before it is indexed. Private registry contents and proprietary
documents are never copied into a new project repository.

The local server cannot guarantee that returned content stays on-device when its
client uses a hosted model. For strict no-egress use, connect it to a local model
and client. This is a client boundary, not a server configuration switch.

## Runtime

- Python 3.11+
- `uv`
- Rust/Cargo only when building from source; released wheels carry the pinned adapter
- GitHub CLI (`gh`) and Git for ticket/project/repository operations
- MCP Python SDK 2.x

The implementation follows the current MCP Python SDK v2 surface: `MCPServer`
with local stdio as the default transport.

## Cloud runtime and deployment direction

The local MCP server is not a hosted cloud service. For the broader KnowB Cloud
runtime and application deployments, see the [Cloud Runtime and Deployment
Strategy](../knowledgeHQ/KnowB%20Cloud%20Runtime%20and%20Deployment%20Strategy.md).
It records the serverless-first direction, Daytona's preferred evaluation role,
Render's demo role, and the conditions under which Railway or Fly.io may be a better
fit.

## Start locally

From the repository root during development:

~~~sh
cargo build --release --locked --manifest-path mcp/okf-bridge/Cargo.toml
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

In verified legacy checkout mode the CLI and local MCP server may load the
checkout-root `.env`. A portable install loads an environment file only when
`KNOWB_ENV_FILE` explicitly names it; existing shell variables always win. The
real `.env` is ignored by git; never put a long-lived credential or refresh token
in it.

If the registry declares `state_dir`, SQLite remains at that path for compatibility.
Otherwise the connector derives an isolated directory under the platform user-state
root using the canonical registry path; `KNOWB_STATE_ROOT` is an absolute test or
operations override. SQLite stores document snapshots and the durable action/audit
ledger; project files remain the knowledge source of truth. Preserve the database
when migrating: it contains pending confirmations and action history. Ranked
retrieval uses `okf-rs`, not SQLite FTS.

### Portable wheel installation

The 0.2.0 release candidate supports macOS ARM64 and Linux x86_64 after their
native wheel and installed-artifact checks pass. macOS x86_64 and Windows x86_64
remain explicitly excluded until their native release evidence is attached; the
full policy is in [`release/support-matrix.yml`](release/support-matrix.yml).

Build a native wheel on each supported target runner. The wheel is non-pure and
contains one target-named `knowb-okf-bridge` executable, so an installed connector
does not need Cargo, Git, `gh`, the website checkout, or network access for local
knowledge work:

~~~sh
uv build --sdist --wheel --project mcp
uv pip install --python /path/to/project/.venv/bin/python mcp/dist/knowb_org_index-*.whl
KNOWB_ORG_CONFIG=/absolute/path/to/registry.yml \
  /path/to/project/.venv/bin/knowb-org doctor
~~~

Use an absolute `KNOWB_ORG_CONFIG` path for a project-folder install. The packaged
adapter is selected before any source-checkout fallback, and an ambient
`knowb-okf-bridge` on `PATH` is never used. `KNOWB_OKF_BRIDGE` remains an explicit
absolute developer override. `doctor` reports adapter source, protocol metadata,
state readiness, synthetic search status, and optional GitHub/design-vault status.

The release workflow produces one exact wheel per target plus `checksums.txt`,
`release-manifest.json`, `sbom.cdx.json`, and `licenses.json`. Publish only those
files after the installed-artifact and rollback gates pass; never rebuild a file
after its checksum is recorded.

## Connect an MCP client

Use the shape in `config/mcp-client.example.json`, replacing the repository path
with its absolute local path. The launch command is:

~~~sh
uv run --project /absolute/path/to/knowb-ai.github.io/mcp knowb-org-mcp
~~~

No HTTP endpoint is created. The MCP host launches this process and communicates
over stdin/stdout.

### Existing knowledgeHQ registry

The portfolio registry remains explicit and stays in the private knowledgeHQ
checkout. Generate an installed-server entry without copying that registry into
the package:

```sh
knowb-org --config /absolute/path/to/knowledgeHQ/.knowb/knowb-ai-portfolio.yml \
  client-config \
  --output /absolute/path/to/knowledgeHQ/mcp/knowb-ai-portfolio.client.json \
  --server-name knowb-ai-portfolio \
  --force
```

Review the generated JSON before applying it to an MCP client. It contains an
absolute `--config` argument and matching `KNOWB_ORG_CONFIG` environment value,
but no credentials or registry contents. `knowb-org-mcp --config PATH` consumes
that entry directly. The command writes a file only when `--output` is supplied;
without it, the generated config is printed for review.

## Knowledge tools

- `doctor` — bounded config, state, adapter, synthetic-search, and capability health report
- `list_projects` — registered projects and optional local candidates
- `discover_local_repos` — bounded inventory of all local organization clones
- `refresh_index` — incremental changed-file refresh
- `search_knowledge` — `okf-rs` ranked full-text search with exact source paths and `knowb://` URIs
- `read_project_doc` — safe allowlisted document retrieval
- `get_project_context` — project map, decisions, documents, ticket references
- `find_related_work` — ticket/query-to-local-knowledge lookup

The optional GitHub policy defaults to enabled for version 1 registries. To run a
knowledge-only connector, add this block; every GitHub read, proposal, confirmation,
and design-vault operation then fails before invoking `gh`, Git, OAuth, Keychain, or
Google Drive:

~~~yaml
capabilities:
  github:
    enabled: false
~~~

## Private design-asset vault

KnowB MCP Atlas design inspiration lives in a private Google Drive folder. This
repository stores the policy and tool boundary, never the real folder ID,
OAuth tokens, refresh tokens, or private asset contents. Configure the ignored
`config/local-projects.yml` from `config/local-projects.example.yml` with:

- `design_assets.enabled: true`
- the private Drive folder ID
- the one allowed Google email address
- the allowed GitHub login(s)
- one or more explicit local upload roots

Configure a Google Desktop OAuth client ID, or point
`KNOWB_GOOGLE_OAUTH_CLIENT_FILE` at the downloaded Desktop OAuth JSON. Then run
the browser approval flow:

~~~sh
uv run --project mcp knowb-org design-assets-auth
uv run --project mcp knowb-org design-assets-verify
~~~

Before the first approval, enable the Google Drive API in a Google Cloud
project and create a Desktop OAuth client. Configure the OAuth consent screen
and add the intended Google account as a test user when the app is in testing
mode. The default full-Drive scope is necessary because this vault reads an
existing private folder and can upload into it; Google may show an unverified-app
warning for an unverified external OAuth project.

The flow uses PKCE and a random `127.0.0.1` loopback callback. It stores only
the refresh grant in the macOS Keychain; short-lived access tokens stay in
memory. No Google access token is accepted as an MCP argument or written to
the audit log.

The MCP tools are:

- `verify_design_asset_vault` — verify both identities and the non-public folder ACL
- `authenticate_design_asset_vault` — start browser consent and store the local grant
- `list_design_assets` — list bounded private descendant metadata
- `read_design_asset` — read one private asset as bounded base64 content
- `propose_design_asset_upload` — preview a local upload without changing Drive
- `confirm_design_asset_upload` — execute one reviewed upload token

The corresponding CLI commands are `design-assets-auth`, `design-assets-verify`,
`design-assets-list`, `design-assets-read`, `design-assets-propose-upload`, and
`design-assets-confirm-upload`. File-level ACLs are rechecked before reads and
after uploads. If a newly uploaded file fails the private ACL check, the tool
removes the file it just created and records the failure.

The repository cannot report that the actual personal folder is private until
the verification command runs with the real local configuration and Google
account. No Google Drive account is connected to the current Codex app session.
See the durable [Design Asset Vault Decision](../knowledgeHQ/Design%20Asset%20Vault%20Decision.md).

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

`seed_documents` may add up to 64 reviewed Markdown files under `docs/` to that same
first commit. It cannot overwrite the required scaffold files or write outside `docs/`.
Use the repository-safe `name` as the GitHub slug and `display_name` for the human-facing
project identity in the README, wiki, contribution guidance, agent instructions, and
local manifest.
Repository visibility and knowledge visibility are intentionally separate: repositories
default to private, and the local MCP knowledge directory is always `local` even when a
future repository is explicitly made public.

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

## Register and enable a local project

Registration and enablement stay two separate operator decisions, and neither is
exposed as an MCP tool: a connected model cannot widen what it is allowed to
index. `register` writes the entry; the project stays inert until `enable`.

~~~sh
knowb-org --config /absolute/path/to/registry.yml register ../../my-project --dry-run
knowb-org --config /absolute/path/to/registry.yml register ../../my-project
knowb-org --config /absolute/path/to/registry.yml enable my-project
~~~

`register` derives `id` and `name` from the project's own `.knowb/project.yml`
when present, falling back to the GitHub remote and then the directory name;
`--id` and `--name` override. `--enabled` registers and enables in one step when
that is the intent. `--dry-run` prints the exact entry without writing.

The operation refuses paths outside `allowed_roots`, refuses a second id for an
already-registered path, and refuses to modify a committed `*.example.yml`.
Re-registering a known project reports `changed: false` rather than appending a
duplicate. Edits are line-scoped so operator comments and ordering survive, the
candidate file is validated by a full registry load before it replaces the
original, and the replacement is atomic — an invalid result leaves the existing
registry untouched. Results report only the affected entry, never the whole
registry.

`disable` is the inverse of `enable` and leaves the entry in place.

## Operator commands

~~~text
knowb-org status
knowb-org discover
knowb-org doctor
knowb-org register PATH [--id ID] [--name NAME] [--enabled] [--dry-run]
knowb-org enable PROJECT [--dry-run]
knowb-org disable PROJECT [--dry-run]
knowb-org index [PROJECT ...]
knowb-org search QUERY [--project PROJECT]
knowb-org read PROJECT PATH
knowb-org context PROJECT
knowb-org manifest PROJECT
knowb-org work [--repo knowb-ai/REPO]
knowb-org ticket knowb-ai/REPO NUMBER
knowb-org github-project NUMBER
knowb-org design-assets-auth
knowb-org design-assets-verify
knowb-org design-assets-list [--limit N]
knowb-org design-assets-read FILE_ID
knowb-org design-assets-propose-upload PATH [--name NAME]
knowb-org design-assets-confirm-upload TOKEN
knowb-org serve
~~~

`scripts/discover-local-repos` is a convenience wrapper around the bounded
discovery command.

## okf-rs retrieval backend

The connector embeds [okf-rs](https://github.com/jyjeanne/okf-rs) through the small
`mcp/okf-bridge` Rust adapter. `Cargo.toml` pins upstream revision
`6d52cc7ad0b5afea2e0001779b4498e268905ddc` (0.7.0); `Cargo.lock` pins the dependency graph.
Build it with the command above. `knowb-org doctor` performs a bounded `--info`
handshake and synthetic search, returning exit code 2 for missing, incompatible, or
unusable adapters. Set `KNOWB_OKF_BRIDGE` to an absolute executable path only for a
developer override. On macOS with a broken Xcode selection, the build hook prefers
`/Library/Developer/CommandLineTools` when present; no global developer-tool setting
needs to change.

Existing MCP tool names, client launch configuration, registry allowlists, document
reads, context results, GitHub confirmations, and design-vault operations remain
available. `search_knowledge` and `find_related_work` now use the Rust backend.
Scores are positive BM25 relevance values, with higher values ranked first; they
are not comparable to the former SQLite scores. `tags` retains its existing role
as additional query terms, rather than a strict metadata filter.

For each search, the connector refreshes selected active projects, exports their
allowlisted document snapshots into a private temporary OKF bundle under
`state_dir`, queries it, and removes the bundle. All selected projects share one
index so their scores are comparable. Stable hashed concept IDs map results back
to original paths and `knowb://` citations, including files named `index.md` and
`log.md`. Original Markdown/frontmatter is retained as the generated concept body;
no authored wiki is rewritten and export does not assert human verification.

Upstream's reader currently accepts language-qualified types only. The adapter's
internal bundle uses its supported `DITA Document` type for documentation; this is
an interoperability label, not an XML import. Upstream search normally indexes
only descriptions/signatures. The bridge supplies the full original Markdown as
in-memory search text, preserving full-body retrieval. A document-count check
fails if the upstream parser silently drops a concept. The protocol returns JSON
IDs/scores, never parsed CLI display text. No source-code generation, enrichment,
embeddings, external network calls, or agent-file rewrites run during retrieval.

The initial backend builds an in-memory index per search, matching the upstream
search API. Large corpora may need a persistent worker after measurement. Missing
binaries, timeouts, or invalid responses fail explicitly; there is no silent SQLite
fallback. Existing SQLite FTS tables, if present, are unused and left intact during
migration along with all action history.

Verify the migration:

```sh
cargo build --release --locked --manifest-path mcp/okf-bridge/Cargo.toml
mcp/.venv/bin/python -m unittest discover -s mcp/tests -v
uv build --sdist --wheel --project mcp
PYTHONPATH=mcp/src mcp/.venv/bin/python mcp/scripts/audit_artifact.py mcp/dist/knowb_org_index-*.whl
```

The real-engine tests require the compiled adapter; CI builds it before testing.

Before changing the shared knowledgeHQ client, stop the existing MCP process and
create an online SQLite backup:

```sh
python mcp/scripts/backup_sqlite.py \
  /absolute/path/to/knowledgeHQ/.knowb-state/org-index.sqlite \
  /absolute/path/to/recovery/knowledgeHQ-org-index.sqlite
```

The backup command reports only schema, table counts, integrity, and a checksum.
Use the preserved registry and backup to rehearse the candidate and to restore the
prior connector if rollback is required. Do not delete the old state or apply an
automatic schema migration.
