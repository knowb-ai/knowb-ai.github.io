# Portable KnowB MCP connector: implementation and test plan

Status: scoped proposal, ready for implementation. Packaging changes described below
are not shipped. Prepared 2026-09-09 following a wheel audit and baseline tests.

## Outcome

A user installs a versioned connector, points it at a project folder, and connects
an MCP client. Documentation search, reads, and project context work without the
KnowB website checkout, a sibling knowledgeHQ clone, Rust/Cargo, or GitHub credentials.
Existing portfolio registries continue to work with the same document boundaries
and durable confirmation history.

The first distribution remains a Python application containing a prebuilt Rust
executable. Python 3.11+ and an installer are prerequisites. A Python-free desktop
application or single native executable is a separate project.

An ordinary installation may download wheels and Python dependencies. Offline
installation requires a prepared wheelhouse containing those dependencies; core
operation after installation must require no downloads or network access.

Source ownership stays in `knowb-ai.github.io/mcp` for this release. Independence
from the website at runtime does not require a repository move. knowledgeHQ owns
the portfolio registry and its client guidance, not a duplicate server.

## Verified starting point

| Evidence | Result | Implication |
| --- | --- | --- |
| `uv build --wheel --project mcp --out-dir /private/tmp/knowb-packaging-audit` | Builds `knowb_org_index-0.1.0-py3-none-any.whl`; 20 archive entries | A successful wheel build alone is insufficient. |
| Wheel archive inspection | No Rust adapter or registry schema packaged | Wheel installation cannot provide complete search today. |
| Import the extracted wheel in a temporary directory, with `KNOWB_*` overrides cleared, then load an explicit valid registry | `Cannot locate the KnowB repository root. Set KNOWB_ORG_ROOT explicitly.` | Even explicit configuration still depends on the website checkout. |
| Adapter lookup from that wheel | Resolves an absent sibling `okf-bridge/target/release/knowb-okf-bridge` | Lookup must use installed package resources. |
| `mcp/.venv/bin/python -m unittest discover -s mcp/tests -v` | 13 tests passed, including real Rust search and in-memory MCP calls | Retain these tests; add installed-artifact and real stdio coverage. |
| Current CI | Builds source and runs tests from the checkout on Linux | It does not establish portable installation or platform support. |

The extracted-wheel check reused installed Python dependencies; it was a targeted
layout reproduction, not a fresh-machine installation test. No Windows, Intel Mac,
or isolated Linux wheel was validated during this planning pass.

Relevant implementation: [packaging](../pyproject.toml),
[configuration](../src/knowb_org_index/config.py),
[environment loading](../src/knowb_org_index/env.py),
[adapter lookup](../src/knowb_org_index/okf.py),
[CLI](../src/knowb_org_index/cli.py),
[MCP startup](../src/knowb_org_index/server.py), and
[existing tests](../tests/test_okf.py).

## Scope and compatibility

Included: platform wheels with the adapter, installation independent of checkout
layout, explicit folder initialization, portable configuration, generated client
configuration, executable health checks, installed-artifact CI, migration guidance,
release artifacts, and rollback verification.

Preserve the current `knowb-org-index` distribution name, `knowb-org` and
`knowb-org-mcp` entry points, MCP knowledge tool names and result fields, explicit
portfolio registries, and `KNOWB_ORG_CONFIG` support. Plan a 0.2.0 release, with
Python/package/server version metadata derived from one source.

No automatic source-code indexing, graph tools, embeddings, enrichment, hosted
HTTP service, background watcher, or wiki conversion is part of this work. No
website assets or private knowledge belong in the wheel. Runtime compatibility
must not depend on the reference paths in the optional KnowB design-remix output.

Plain folders need no Git repository or organization identity for knowledge reads.
GitHub and design-vault operations remain explicit optional capabilities. New folder
configurations default them off; existing portfolio behavior is preserved through
a compatibility default. Core startup and search must not probe credentials or
require `gh`, Git, Google OAuth, or macOS Keychain. Enabling optional capabilities
must retain proposal/confirmation checks. Porting Keychain-backed OAuth to Windows
or Linux is excluded; report that capability as unavailable there without breaking
knowledge tools.

## Intended user contract

These commands describe the target API, not commands available in 0.1.0:

```sh
# Install a tested platform wheel from the chosen distribution channel.
python -m pip install --only-binary=:all: /path/to/knowb_org_index-0.2.0-PLATFORM.whl

knowb-org init /absolute/path/to/project
knowb-org --project-dir /absolute/path/to/project doctor
knowb-org client-config /absolute/path/to/project
```

The emitted client entry launches the installed `knowb-org-mcp` executable with
`--project-dir /absolute/path/to/project`. It includes absolute executable and
folder paths, so it works from an unrelated client working directory. Paths are
JSON argument-array elements, never shell-interpolated command strings. It contains
no credentials and is printed for the user to put in their MCP client settings.

`init` creates `.knowb/connector.yml` with paths relative to that configuration and
one explicitly registered project. A valid existing `.knowb/project.yml` supplies
identity and documentation policy. Otherwise derive a stable local ID from the
folder name, with an explicit `--id` override, and configure root Markdown plus
standard documentation directories. Print the exact selected roots and exclusions;
never register parent or sibling folders implicitly. No recursive all-file policy.

Do not overwrite manifests, existing connector config, `.env`, `AGENTS.md`, or
authored documents. Re-running `init` against a compatible configuration is a no-op;
conflicting or malformed configuration produces an actionable error. Empty folders
are valid and report zero documents. Initialization changes only the connector
config; cached state is kept outside the project by default.

`--project-dir` and explicit `--config` are mutually exclusive. Explicit arguments
win over environment defaults: an explicit folder cannot accidentally select the
user's portfolio through `KNOWB_ORG_CONFIG`. With neither argument, retain explicit
`KNOWB_ORG_CONFIG`, then recognize `.knowb/connector.yml` in the current folder.
Do not walk arbitrary ancestors to choose a project. Uninitialized folders get the
precise initialization command, not an implicit broad registry.

## Implementation sequence and exit gates

### P1 — Package the existing Rust adapter

Files: `mcp/pyproject.toml`, a build hook, `okf-bridge/Cargo.toml`/`Cargo.lock`,
package resources, and initial artifact-inspection tests.

Keep Hatchling initially. A build hook compiles the pinned adapter with
`cargo build --release --locked`, includes it under `knowb_org_index/_bin/`, and
emits platform-specific wheel metadata with `pure_python=false`. Validate the
actual OS/architecture and minimum OS/ABI tag; never ship native contents in a
`py3-none-any` wheel. The standalone subprocess has no Python extension ABI, so
avoid unnecessarily coupling each binary build to one CPython minor version.

Include runtime schemas/default templates and required license notices. The sdist
must contain the hook, Cargo files, lockfile, and Rust source; test a wheel built
from the sdist. Compilers are build-time requirements only. Native dependencies
must be inspected on every target, particularly Linux glibc and Windows runtimes.
Do not claim compatibility by changing a filename tag without testing its binary.

Hatch documents build-hook wheel inclusion and platform metadata controls in its
[wheel reference](https://hatch.pypa.io/latest/plugins/builder/wheel/) and
[build-hook reference](https://hatch.pypa.io/latest/plugins/build-hook/reference/).
These provide the proposed mechanism, not proof that our adapter is portable.

Exit gate: a correctly tagged wheel contains exactly the expected native adapter;
that adapter executes from an extracted/installed package outside the checkout.
Resolve any build-backend or native-dependency problem here before expanding CI.

### P2 — Remove runtime checkout dependencies

Files: `config.py`, `models.py`, `env.py`, `okf.py`, `service.py`.

Separate configuration location, project root, application resources, and state
location. Loading an explicit registry must never call website-root discovery.
Read packaged resources through the package resource API, not `__file__.parents`
assumptions. Preserve legacy website discovery only as a deliberate compatibility
path, not a requirement for installed applications.

Use a platform-appropriate user state directory keyed by the canonical config
location for new installations. Preserve explicitly configured existing
`state_dir` exactly. Different configs must not share pending actions. Moving a
folder changes a default state key; disclose this and support an explicit stable
state location. No automatic relocation or deletion of audit databases.

Use the bundled adapter by default. Keep `KNOWB_OKF_BRIDGE` as an explicit developer
override, require an absolute executable path, and verify the same protocol.
Remove ambient PATH preference so an unrelated stale binary cannot replace the
packaged version. Development builds may use a documented explicit override.

Do not load an arbitrary project's `.env` merely because it was selected for
reading. Preserve process-environment precedence and explicit `KNOWB_ENV_FILE`;
retain legacy checkout `.env` behavior only in the documented legacy mode.

Exit gate: installed search runs with no checkout, no `KNOWB_ORG_ROOT`, no Cargo,
no Git/`gh`, and an unrelated working directory. Legacy portfolio configuration
loads the same IDs, allowlists, state directory, and existing confirmation records.

### P3 — Add folder initialization and client configuration

Files: `cli.py`, `server.py`, configuration helpers, packaged schemas/templates.

Implement the user contract above. Parse explicit MCP startup arguments before
constructing the service. Normalize Windows/POSIX paths, verify containment after
resolution, handle spaces and Unicode, and preserve existing allowlist semantics.
The generated client entry must work without a globally discoverable executable
on PATH. Installation relocation requires regenerating its absolute launch path.

For legacy registries, support `knowb-org --config PATH client-config` and generate
an installed-server launch with `--config PATH`. Adding further portfolio projects
continues to require explicit registry entries; single-folder init does not need a
second portfolio-management interface.

Exit gate: repeated init is harmless; a real MCP client can use the generated
configuration to initialize, list tools, search, and read an original document.
Core stdio emits only protocol messages; diagnostics go to stderr.

### P4 — Health, failure handling, and capability boundaries

Files: diagnostics in `okf.py`, CLI doctor, service construction, optional tool setup.

Extend the adapter's version handshake with protocol version, adapter version,
upstream revision, and build target. Doctor verifies execution, not just file
existence: run a bounded synthetic search, check the configuration, state-directory
writability, and return JSON plus nonzero status on core failures. Use only synthetic
text for the adapter self-test.

Cover missing/non-executable/wrong-architecture binaries, protocol mismatches,
timeouts, malformed JSON, unavailable roots, and unwritable state. Keep errors
actionable without returning source text or credentials. Optional unavailable
services are reported separately and do not make knowledge-only doctor fail.

Exit gate: every failure has a tested error/exit path; disabled optional capabilities
cannot execute network or mutation operations, even if invoked by tool name.

### P5 — Installed-artifact and platform test matrix

Files: new packaging/stdio tests and dedicated CI jobs alongside existing tests.

Release targets proposed for this scope:

| Platform | Build/test requirement |
| --- | --- |
| macOS ARM64 | Native build and install test; declare the tested minimum macOS version. |
| macOS x86_64 | Separate native artifact and execution test; no untested universal tag. |
| Linux x86_64 | Build/test against a declared glibc baseline, initially targeting manylinux_2_28; verify shared dependencies. |
| Windows x86_64 | Native `.exe` packaging and stdio tests; no Keychain requirement for core tools. |

Run the installed Python package on 3.11, 3.12, 3.13, and 3.14 for each claimed
platform. Build each native artifact once per target, then reuse it across Python
tests. Exclude Linux ARM64, musl/Alpine, and Windows ARM64 from the initial support
claim. If a listed target cannot pass, the release is blocked for that target;
reducing the advertised support matrix must be an explicit scope decision.

Artifact tests use a fresh environment, installed wheel, sanitized environment,
unrelated cwd, and no source checkout on import paths. Disable editable installs
and clear `PYTHONPATH`. A dedicated stdio subprocess test launches the exact
generated command; in-memory MCP tests do not satisfy this gate. Real-engine
tests must fail, rather than skip, if a release artifact lacks its binary.

### P6 — Release and portfolio migration

Files: release workflow, installation guide, executable connector README,
knowledgeHQ MCP README and client example.

Produce versioned wheels, sdist, SHA-256 checksums, dependency/license inventory,
upstream revision, and test evidence. Stage CI artifacts first. Install the exact
staged wheel in the final smoke test; do not rebuild a different artifact for
publication. Gate release on P1–P5 and the acceptance matrix below.

Keep installation possible from a downloaded wheel. Choose the package-index
destination and verify name ownership before adding an index-based one-line
install command to user guidance. Publishing releases/packages, provisioning
credentials, and changing client settings are separate execution actions; this
planning task does not perform them.

Migrate the knowledgeHQ client command to the installed executable while retaining
its explicit existing registry. Stop existing processes before any state migration;
prefer no database-schema change in this release. If one becomes necessary, back
up with SQLite's backup API rather than copying a live database without its WAL.
Smoke-test indexed documents and pending-action idempotency, then test reinstalling
the prior working distribution/checkout against the preserved state.

Exit gate: the release candidate installs and connects on all declared targets;
knowledgeHQ uses the same corpus and state; rollback is demonstrated. No running
client is changed silently and no private registry is included in public artifacts.

## Acceptance matrix

| ID | Test | Required result |
| --- | --- | --- |
| A01 | Inspect wheel and sdist | Binary, source/build inputs, templates, license notices present; platform metadata correct; no knowledge, credentials, state DB, or website output. |
| A02 | Fresh install with compilers/Git/checkout absent | Native adapter and Python entry points work; no build or runtime download. |
| A03 | Explicit config from unrelated cwd | Starts without website-root discovery or ambient config. |
| A04 | Init plain and empty folders twice | Deterministic config/no-op repeat; no writes to authored files; empty results are valid. |
| A05 | Existing manifest/config, malformed YAML, conflicting flags | Preserve valid policy; reject conflict/corruption clearly; no silent overwrite. |
| A06 | Spaces, Unicode, duplicate basenames, Windows drive paths | Stable project/path identity and correct original citations; safe argument arrays. |
| A07 | Traversal, symlinks/junctions, excluded/private files, oversized files, siblings | Content stays within selected policy; revoked projects/docs disappear from reads and search. |
| A08 | Installed real-engine full-body retrieval | Finds a term deep in body, including original `index.md`/`log.md`; obeys project/limit filters. |
| A09 | Add/edit/delete/disable after indexing | Next refresh/search reflects source and policy; no stale disclosure. |
| A10 | Generated config through real stdio MCP process | Initialize/list/search/read/context succeed; stdout remains protocol-only; shutdown cleans up. |
| A11 | Missing/corrupt/wrong-arch adapter, protocol mismatch, timeout | Bounded explicit error; doctor fails core health; no SQLite search fallback. |
| A12 | Two concurrent clients, locked DB, interrupted child | No cross-request bundle leakage; bounded failure/retry; temp resources cleaned after normal failure. |
| A13 | Legacy registry and confirmation ledger | Same IDs/allowlists/paths; pending actions persist; replay cannot duplicate a mutation. |
| A14 | Offline core operation and optional capability calls | Search uses no network; optional disabled tools fail before external calls; no credential requirement. |
| A15 | State permissions, two configs, moving folder, upgrade/downgrade | Defined state ownership/isolation; no silent loss or migration of audit history. |
| A16 | Every supported platform/Python combination | Installed-artifact tests pass with zero missing-adapter skips. |

For A07, use OS-native fixtures rather than assuming POSIX symlink behavior on
Windows. For A12, hard process termination may leave a temporary bundle: define
safe startup cleanup of abandoned connector-owned temp directories without touching
live requests or the durable ledger. Do not broaden cleanup to arbitrary state files.

Measure cold/warm startup and search on a fixed public synthetic corpus (100 and
1,000 Markdown files), recording machine, corpus bytes, p50/p95, and peak memory.
Set a documented regression threshold from that baseline before the release gate.
Do not make a universal latency claim from the existing local smoke test. Persistent
index caching is follow-up work unless measurements show the per-query build cannot
meet the agreed threshold.

## Delivery order, estimates, and completion rule

Suggested reviewable changes: P1 packaging proof → P2 runtime decoupling → P3 folder
onboarding → P4 health/capability boundaries → P5 artifact CI → P6 release/migration.
Tests for each change land with it; P5 expands coverage across platforms rather
than postponing testing. Every change must keep the existing 13-test suite passing.

Planning estimate: 8–13 focused engineering days including native packaging and
platform debugging; platform-runner access and release-account setup can add elapsed
time. This is an estimate, not a delivery promise. No owners or tickets are assigned
by this document.

Done means a user can install a tested wheel, initialize an unrelated folder,
paste generated client configuration, and retrieve an original document through
MCP without the website checkout or compiler; the same artifact passes A01–A16 and
the existing knowledgeHQ portfolio can migrate and roll back without losing state.
Passing checkout tests or producing a wheel alone does not satisfy completion.
