# Portable connector P6: release and knowledgeHQ migration

Execution plan for [issue #9](https://github.com/knowb-ai/knowb-ai.github.io/issues/9).

Branch: `codex/portable-release-migration`

Baseline: `main` at `6564302`, including the merged P1–P5 implementation from
PR #11. This plan is deliberately release-first: no package publication,
credential setup, live client replacement, or state rewrite happens until the
corresponding evidence and approval gate are complete.

## Outcome

Ship one immutable, versioned connector release whose exact tested artifacts can
be installed outside the website checkout. Migrate the existing knowledgeHQ MCP
entry to launch that installed connector with the same explicit registry,
allowlisted projects, citations, exclusions, and SQLite action ledger. Prove a
rollback using preserved state before calling the migration complete.

The release is complete only when a clean installation can initialize or load a
folder, start the real MCP stdio server, search and read an original document,
and return project context without the website checkout, Cargo, Git, `gh`, or
runtime network access.

## Current baseline and known gaps

- The connector source and native bridge live in `knowb-ai.github.io/mcp`.
- P1–P5 code and tests are on `main`; issue #9 is the remaining open epic ticket.
- Package metadata and the Python module currently report `0.1.0`. The release
  candidate should use one agreed version (proposed: `0.2.0`) across Python,
  Cargo metadata, the MCP server, filenames, and release notes.
- The existing portable CI proves Ubuntu and macOS jobs for Python 3.11 and
  3.14. It does not yet prove Windows, macOS x86_64, Linux glibc baseline, or
  Python 3.12/3.13. Those targets must either gain native evidence or be
  explicitly excluded from the release support matrix.
- The knowledgeHQ client example still launches `uv run` from the checkout and
  points at `.knowb/knowb-ai-portfolio.yml`. Its registry and explicit
  `../.knowb-state` path are the compatibility source of truth.
- The current `client-config` flow is designed for a single onboarded folder.
  P6 must add or document the legacy-registry form that emits an installed
  `knowb-org-mcp --config <absolute-registry>` command without copying the
  private registry into the public package.

## Release decisions required before implementation

Record these decisions in the release record before changing user-facing
installation guidance:

1. Distribution channel and package ownership: GitHub release assets, an index,
   or both. Verify the package name is available and the account that may
   publish it.
2. Release version, Python minimum, OS minimums, supported architecture list,
   Linux ABI baseline, and the accountable release owner.
3. Whether the first release supports only the currently evidenced targets or
   blocks until Windows, Intel macOS, Linux ABI, and all claimed Python minors
   are certified.
4. State-directory policy: retain knowledgeHQ's explicit state path exactly;
   document the default user-state behavior for newly initialized folders.
5. Approval owners for public artifact publication and for changing the shared
   knowledgeHQ client configuration. They are separate approvals.

## Workstreams and exit gates

### 1. Freeze the release contract

Create a release manifest that names the version, source commit, okf-rs revision,
Rust target, Python range, OS/architecture support, package filename patterns,
and every artifact checksum. Derive runtime version information from one source
where possible and fail CI when metadata disagrees.

Exit gate: a reviewer can determine exactly which source, dependency lockfiles,
native targets, and support claims produced the candidate.

### 2. Make release artifacts reproducible and inspectable

Add a release workflow that builds each native target once, uses locked
dependencies, and preserves the resulting wheel and sdist as immutable CI
artifacts. Generate, alongside them:

- SHA-256 checksums over the exact files to publish;
- Python dependency inventory from `pyproject.toml`/`uv.lock`;
- Rust dependency inventory from `Cargo.lock` and `cargo metadata`;
- an SBOM in a reviewable standard format;
- license and notice inventory, including the pinned `okf-rs` crates;
- upstream revision, compiler/toolchain, target, and build-environment metadata;
- a release note draft with support, exclusions, optional capability limits,
  state handling, and recovery commands.

Audit the sdist and every wheel for private paths, credentials, registry YAML,
SQLite databases/WAL files, source corpora, `.env` files, and website build
output. Do not rebuild after checksums are generated; publication consumes the
staged files byte-for-byte.

Exit gate: artifact audit is clean, metadata is internally consistent, and the
staged files are reproducible from the recorded source and lockfiles.

### 3. Certify the exact staged artifacts

For each claimed target, install the exact staged wheel in a fresh environment
with an unrelated current directory and a sanitized environment. Remove the
checkout, Cargo, Git, `gh`, and network access from the test path. Run the full
P1–P5 tests plus the installed-artifact matrix:

- initialize plain, empty, existing, malformed, and conflicting folders;
- generate and inspect client configuration with spaces and Unicode paths;
- launch the exact MCP stdio subprocess and exercise initialize, tool listing,
  search, read, and context;
- run deep-body retrieval and verify original source paths and `knowb://` URIs;
- verify disabled projects, exclusions, traversal, symlink, size, and stale-file
  behavior;
- verify missing, non-executable, wrong-target, protocol-mismatch, timeout,
  malformed-response, and unwritable-state failures;
- prove offline search and prove disabled optional capabilities fail before any
  external process or credential lookup;
- record cold/warm startup, search p50/p95, corpus size, and peak memory on a
  fixed synthetic corpus.

Exit gate: every advertised platform/Python combination passes without an
adapter-missing skip. If a target is not certified, remove it from the release
claim before publication and record the decision.

### 4. Rehearse the knowledgeHQ migration without touching the live client

Use a disposable copy of the current knowledgeHQ checkout and a stopped MCP
process. Capture a pre-migration compatibility record containing:

- registry path and SHA-256, project IDs, enabled/disabled state, resolved paths,
  knowledge roots, excludes, forbidden paths, and document counts;
- representative citation records for root and deep documents;
- SQLite schema version, WAL/shm presence, pending-action rows, audit events,
  and idempotency keys (metadata only; never publish document contents);
- the currently working checkout launch command and connector version.

Back up the live ledger with SQLite's online backup API while the process is
stopped. Verify the backup opens read-only, has the expected schema and row
counts, and is stored outside any public artifact or repository. Do not use a
raw file copy when a WAL may be active.

Extend the legacy `client-config` path to generate an installed-server command
against the existing absolute registry. Keep the registry content and explicit
project list unchanged. Review the generated JSON before applying it.

Exit gate: the candidate can read the same projects and citations from the
disposable copy, and the backup can be opened independently with matching
ledger fingerprints.

### 5. Execute the controlled migration

Only after the release and rehearsal gates pass:

1. Stop the running MCP client/server and record the stop time and prior command.
2. Take the final SQLite online backup and record its checksum.
3. Install the exact staged wheel into the approved environment.
4. Generate the knowledgeHQ client entry with absolute executable and registry
   paths; review it, then apply it as a separate approved change.
5. Start the candidate over stdio and run `doctor`, index refresh, search, read,
   context, and audit-log checks. Use the same query/document fixtures as the
   pre-migration record.
6. Confirm no package file contains the private registry, credentials, state
   database, or indexed document body.
7. Attach command output, checksums, artifact names, ledger fingerprints, and
   the support matrix to the release record.

No schema migration, automatic project discovery, credential provisioning,
client restart, or destructive cleanup is permitted in this step.

Exit gate: knowledgeHQ operates through the installed executable with unchanged
policy and state, and all observed differences are either empty or explicitly
approved and documented.

### 6. Demonstrate rollback and close the release

In an isolated environment, reinstall the prior working checkout/distribution
and point it at the preserved registry and SQLite backup. Verify:

- the prior connector opens the backup and reports the original schema;
- indexed reads and representative citations still resolve to the same files;
- pending confirmations remain pending, completed actions remain replay-safe,
  expired actions remain expired, and audit history is intact;
- no mutation is executed twice when a completed confirmation is replayed;
- the candidate can be reinstalled without deleting or rewriting the backup.

Publish only the exact staged files after the rollback evidence is attached.
Update the executable connector README and the knowledgeHQ MCP README/client
example in their respective reviewed changes. Release notes must include the
adapter revision, support/exclusion matrix, offline behavior, state location,
backup method, rollback commands, and known optional-capability limitations.

Exit gate: a reviewer can restore the previous connector using the release
record alone, and the release record contains all acceptance evidence.

## Proposed commit sequence

Keep each commit independently reviewable and green:

1. `release: define version and support manifest` — version source, release
   metadata, target policy, and decision record.
2. `build: add reproducible release provenance` — workflow, staged artifacts,
   checksums, SBOM/dependency/license reports, and artifact audit.
3. `test: certify exact staged artifacts` — fresh-install, real-stdio, offline,
   and A01–A16 evidence harness.
4. `feat: generate installed command for legacy registries` — explicit
   knowledgeHQ config support with no policy or registry-copy behavior changes.
5. `docs: document installation and migration recovery` — connector and
   knowledgeHQ guidance, support matrix, state and rollback procedures.
6. `release: attach migration and rollback evidence` — checked-in redacted
   evidence/index only; never commit credentials, private registry data, SQLite,
   or source corpus.

If a platform runner or distribution account is unavailable, stop at the exact
gate, record the blocker, and do not weaken the support claim to make CI green.

## Acceptance matrix mapped to evidence

| Issue criterion | Evidence required |
| --- | --- |
| Exact clean release artifacts | Staged-file manifest, checksums, SBOM, license report, and private-content audit |
| Clean installation and offline MCP use | Fresh venv/stdout protocol transcript with checkout/Cargo/Git/network removed |
| knowledgeHQ guidance uses installed connector | Reviewed client JSON and real subprocess run against the unchanged registry |
| Policy, citations, exclusions, disabled projects unchanged | Before/after compatibility record and representative search/read/context diff |
| Ledger and replay safety preserved | SQLite online-backup checksum, row/schema fingerprints, proposal/confirm/replay/audit tests |
| Rollback demonstrated | Isolated prior-version run against preserved backup with matching citations and ledger |
| Release notes complete | Versioned notes covering support, adapter revision, state, optional capabilities, and recovery |
| No unreviewed side effects | Separate approvals and an execution log showing no credential setup, silent restart, or publication before gate |

## Risks and controls

- **Uncertified native target:** block publication for that target or remove it
  explicitly from support; never relabel an untested binary.
- **Artifact drift:** checksum before publication and compare the downloaded
  file to the staged checksum; never rebuild between test and publish.
- **Private data leakage:** fail the archive audit on registry names, path
  fragments, credentials, SQLite signatures, or source-corpus content.
- **Ledger loss or duplication:** stop the process, use SQLite backup API, keep
  the old state immutable, and test concurrent/replayed confirmations.
- **Policy drift:** compare normalized registry/project/allowlist fingerprints
  before and after; reject any unapproved difference.
- **Irreversible client change:** review the generated JSON separately and keep
  the previous file and launch command in the rollback record.

## Definition of done

Issue #9 can close when the release owner has approved the support and
distribution decisions, every claimed artifact has passed A01–A16, the exact
staged files are published, knowledgeHQ runs them with its original registry and
ledger, rollback has been demonstrated, and the release record contains the
checksums, inventories, transcripts, compatibility comparison, and recovery
instructions. A passing checkout build or a wheel that merely exists is not
sufficient.
