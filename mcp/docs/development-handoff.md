# KnowB MCP development handoff

The public `knowb-org-index` 0.2.0 release remains available in this repository.
The private KnowB company connector is moving to the knowledgeHQ repository so
its executable, registry policy, and canonical knowledge can evolve together.
This handoff does not change the published artifact, its support claim, or an
existing client's command. It does not make company knowledge public.

## Source and compatibility baseline

The source snapshot for the private copy is public commit
`0972c3d3994990def79f9a7b0d3f1c71dd83139a`, the merge
of [memo-review PR #19](https://github.com/knowb-ai/knowb-ai.github.io/pull/19).
It includes the formal memo review gate from [issue #17](https://github.com/knowb-ai/knowb-ai.github.io/issues/17).
The published release remains tag
[`mcp-v0.2.0`](https://github.com/knowb-ai/knowb-ai.github.io/releases/tag/mcp-v0.2.0);
its artifact hashes, pinned adapter revision, and supported targets are recorded
in the [0.2.0 release record](releases/0.2.0.md) and
[`support-matrix.yml`](../release/support-matrix.yml). The post-release source
snapshot is a development baseline, not a retroactive change to 0.2.0.

The handoff includes these public source contracts:

| Contract | Public location |
| --- | --- |
| CLI, MCP server, local index, GitHub boundary, and memo review | `mcp/src/knowb_org_index/` |
| Python package and native build hook | `mcp/pyproject.toml`, `mcp/hatch_build.py`, `mcp/uv.lock` |
| Pinned search adapter and protocol | `mcp/okf-bridge/` |
| Connector, protocol, release, and portability tests | `mcp/tests/` |
| Artifact and recovery scripts | `mcp/scripts/` |
| Public CI and manual release workflow | `.github/workflows/test-mcp.yml`, `test-mcp-portable.yml`, `release-mcp.yml` |
| Client shape and project-side contract | `config/mcp-client.example.json`, generated `.knowb/mcp-client.example.json`, `AGENTS.md`, and validation guide |

The package entry points are `knowb-org` and `knowb-org-mcp`. Existing local
registries remain external configuration; source code does not include the
private registry, document corpus, credentials, or SQLite state. The project
creation contract remains `.knowb/project.yml`, `.knowb/mcp-client.example.json`,
MCP-first `AGENTS.md`, and `docs/operations/knowb-mcp-validation.md`.

## Validation and transition

The private copy is under review in
[knowledgeHQ PR #10](https://github.com/knowb-ai/knowledgeHQ/pull/10). Its
equivalent test and client checks must pass before switching an active client.
The public 0.2.0 command remains the supported fallback until the private copy
is accepted and the client transition is verified. A client migration is an
explicit, separate operation; merging the source handoff alone does not switch
running clients.

Before switching, record the current command, release version, registry path,
adapter metadata, project and allowlist fingerprints, and audit/pending counts.
Stop the running MCP process. Use `mcp/scripts/backup_sqlite.py` to make an online
backup of the state database and verify its checksum and integrity. Preserve the
old client entry and the backup. Configure the new client with the private
checkout's `knowb-org-mcp` entry point and the same explicit registry path.

Run `doctor`, project context, targeted search, exact document read, and audit
checks through the new local stdio command. Compare project IDs, enabled states,
roots, excludes, citations, pending confirmations, and audit history with the
pre-switch record. Rehearse the preserved command and database in an isolated
environment before closing the cutover. The detailed state and rollback sequence
is in the [knowledgeHQ migration checklist](knowledgehq-migration-checklist.md).

If the private command fails acceptance, restore the preserved public command
and compatible state backup; do not delete or rewrite the live database to make
the new command pass. The published wheel can also be installed without this
website checkout for local knowledge operations.

## Public maintenance status

This repository retains the published package, release evidence, tests, and
manual release workflow for compatibility and recovery. New company-brain work
belongs in private knowledgeHQ. A future public connector release requires an
explicit release decision and fresh artifact/platform acceptance; the move does
not silently publish private features or change the 0.2.0 support matrix.
