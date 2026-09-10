# Portable connector core implementation plan

Branch: `codex/portable-connector-implementation`

Issues:

- [#4 — package the okf-rs adapter](https://github.com/knowb-ai/knowb-ai.github.io/issues/4)
- [#5 — decouple runtime from the website checkout](https://github.com/knowb-ai/knowb-ai.github.io/issues/5)
- [#7 — add health checks and capability-boundary failures](https://github.com/knowb-ai/knowb-ai.github.io/issues/7)

Status: implementation-ready plan. This branch establishes the installable core.
Project-folder initialization remains in #6, the complete platform/Python test
matrix remains in #8, and publication plus knowledgeHQ migration remains in #9.

## Delivery outcome

At the end of this branch, a platform wheel built from the connector source contains
the pinned `okf-rs` adapter, can be installed into a clean environment, and can load
an explicit portfolio registry from any working directory. Search, document reads,
project context, and `doctor` work without a website checkout, Cargo, Git, `gh`, or
network access at runtime. Existing knowledgeHQ configuration, allowlists, source
citations, and confirmation/audit state remain compatible.

This branch will not publish a release, switch a running MCP client, generate
single-folder config, or alter knowledgeHQ state. It produces the code and local
artifact evidence needed for those later stages.

## Design decisions

### Distribution shape

Keep one Python distribution, `knowb-org-index`, with two console entry points:
`knowb-org` and `knowb-org-mcp`. Ship `knowb-okf-bridge` as package data inside a
platform wheel. It is a subprocess with a versioned JSON protocol, not a Python
extension, so the wheel should use a Python-independent ABI tag for the target
platform rather than a CPython-minor ABI tag.

Keep Hatchling for this branch. Add a custom build hook that:

1. obtains the target from an explicit build variable or the current native target;
2. invokes Cargo with `--release --locked` against `okf-bridge/Cargo.toml`;
3. copies exactly one adapter into `knowb_org_index/_bin/` under a deterministic
   target-specific name;
4. marks the wheel as non-pure and supplies the correct platform tag;
5. records the included artifact for build cleanup without deleting developer
   outputs or unrelated files; and
6. includes Cargo source, the lockfile, build hook, schemas, and licenses in the
   sdist so a wheel can be built from the sdist.

Each target runner will build its own native wheel. Cross-compiling a universal
wheel is not part of this branch. Issue #8 must execute the complete declared
platform/Python matrix before release. The build hook must already reject unknown
or inconsistent target/tag combinations so #8 cannot publish misleading artifacts.

### Adapter lookup

Replace the current lookup order of environment → PATH → checkout target with:

1. an explicit absolute `KNOWB_OKF_BRIDGE` developer override;
2. the adapter installed in package resources; and
3. a clearly identified checkout build only when running from a verified source
   layout.

Do not search ambient PATH. A stale executable with the same name must never shadow
the packaged adapter. Resolve package resources through `importlib.resources`. The
normal wheel-install path is an extracted executable file; if the import loader does
not provide a real executable path, return an unsupported-installation error rather
than copying a native binary to an uncontrolled location.

On POSIX, verify the resource is a regular executable file. On Windows, require the
`.exe` resource. Reject a relative override, directory, symlink escape, or file that
fails the protocol handshake. Diagnostics may report the selected source
(`override`, `package`, or `checkout`) and target, but must not report environment
values or arbitrary subprocess stderr.

### Versioned bridge protocol

Retain search protocol version 1 for compatibility and add a machine-readable
`--info` operation. Its bounded JSON response contains:

```json
{
  "protocol": 1,
  "adapter_version": "0.2.0",
  "okf_rs_revision": "6d52cc7ad0b5afea2e0001779b4498e268905ddc",
  "build_target": "aarch64-apple-darwin",
  "max_request_bytes": 65536,
  "max_query_bytes": 16384,
  "max_results": 50
}
```

Generate `build_target` from Cargo's `TARGET` through a small build script; do not
infer it at runtime. Keep `--version` for people, backed by the same constants.
Python must validate required fields, exact protocol support, expected revision,
numeric bounds, output size, exit status, and timeout before using the adapter.

Search input remains JSON on stdin. Search output remains a JSON object containing
`protocol` and `results`. Both directions retain size limits. Adapter failures are
classified in Python as missing, not executable, handshake timeout, incompatible,
search timeout, failed execution, or invalid response. User-facing errors stay
bounded and never include a generated OKF snapshot or source text.

### Configuration and checkout independence

Refactor configuration resolution into explicit concepts:

- `config_path`: canonical path to the selected registry;
- `config_base`: directory used for relative paths in that registry;
- `legacy_checkout_root`: optional verified source-layout root;
- `state_dir`: explicit registry value or derived user-state location; and
- package resources: schemas/templates bundled in the installed distribution.

`load_registry(config_path)` must not call checkout discovery when `config_path` is
provided. When it is omitted, resolution order is:

1. `KNOWB_ORG_CONFIG`, when set;
2. the current checkout's local/example config, only after verifying the checkout
   fingerprint; and
3. an actionable missing-config error.

Do not scan arbitrary ancestors or use installed `site-packages` as a repository
root. Preserve `Registry.repository_root` during this compatibility release, but set
it to the verified legacy checkout root or the explicit config base. No current
runtime behavior may depend on it when an explicit registry is used.

### State directory

If `state_dir` is present in a registry, resolve it relative to the config exactly as
today. This preserves knowledgeHQ's database path and confirmation history.

If it is absent, derive a directory below a platform user-state root. Use a stable
key formed from the SHA-256 of the canonical config path, not registry contents, so
ordinary edits do not create a new ledger. Add `KNOWB_STATE_ROOT` as an absolute
test/operations override for the user-state root. Two configs must receive different
state directories. Never migrate, merge, delete, or rewrite an existing database in
this branch.

SQLite schema stays unchanged. Existing unused FTS tables remain untouched. Opening
the database must preserve pending actions, audit events, expiry, claim atomicity,
and idempotent replay.

### Environment loading

An installed connector must not load `.env` from `site-packages`, the selected
project, or the current directory. Load an environment file only when:

- `KNOWB_ENV_FILE` explicitly selects it; or
- verified legacy checkout mode selects the checkout-root `.env`.

Existing process variables always win. Parse errors name the environment file and
line while excluding values. Core startup must not read OAuth client files, macOS
Keychain, GitHub authentication, or repository contents before the registry policy
has been validated.

### Health and optional capabilities

Move health behavior from the CLI into `OrgIndexService.doctor()` so CLI and tests
exercise one implementation. Doctor returns structured sections:

- `config`: selected path, parse status, and registry summary;
- `state`: path, directory/write probe, database open status, and schema version;
- `search`: adapter source, handshake metadata, and synthetic search result;
- `capabilities`: local knowledge, GitHub, and design-vault readiness; and
- `ok`: true only when core config, state, and local search are healthy.

The search self-test creates one synthetic Markdown concept in a private temporary
directory, searches for a unique fixed token, validates one matching result, and
cleans up. It never exports a real project document and uses strict time/output
limits.

Add an explicit GitHub capability policy to the registry model. For existing version
1 registries with no capability block, preserve the current enabled behavior. A
registry may set GitHub capability to disabled; every public GitHub operation must
then fail through one central guard before `gh`, Git, network, proposal creation, or
confirmation execution. Design assets already have an enabled guard; expand tests
to prove every public entry point crosses it before OAuth, Keychain, Drive, or `gh`.

Missing Git, `gh`, credentials, or platform-specific Keychain support is optional
capability status and does not fail knowledge-only doctor. An invalid knowledge
policy, unwritable state, missing/incompatible adapter, or failed synthetic search
does fail doctor with exit code 2.

Stdio startup should validate configuration and state but should not run the full
synthetic doctor on every client connection. MCP stdout remains protocol-only.

## Implementation sequence

### Change 1 — Freeze contracts and fixtures

Add test helpers for isolated registries, legacy SQLite state, built-wheel
inspection, sanitized environments, subprocess output bounds, and a synthetic OKF
bundle. Capture the current knowledgeHQ project IDs, active states, selected paths,
and representative citations in a compatibility fixture that contains no private
document contents.

Exit gate:

- current 13 tests pass;
- compatibility fixture demonstrates the current behavior;
- negative adapter and state fixtures fail for the expected reason; and
- no production behavior changes yet.

### Change 2 — Version the adapter protocol

Add Cargo build-target metadata, `--info`, shared protocol constants, bounded output,
and Rust unit/integration tests. Implement the Python handshake parser and typed
adapter errors without changing lookup order yet.

Exit gate:

- Rust format, clippy, and tests pass;
- Python accepts the expected handshake and rejects missing fields, wrong protocol,
  wrong revision, oversized output, timeout, and malformed JSON; and
- current real-engine search tests pass through protocol 1.

### Change 3 — Build platform wheels

Add the Hatch build hook, package-resource directory, sdist inclusions, license
files, platform tag validation, and artifact inspection test. Build a native wheel
and an sdist locally. Build a second wheel from the sdist.

Exit gate:

- wheel metadata is non-pure and platform-specific;
- exactly one target adapter is included and executable;
- the source checkout/target directory is not required after installation;
- wheel and sdist contain no registry, corpus, SQLite state, credentials, or site
  output; and
- clean install can execute `--info` with Cargo hidden from PATH.

### Change 4 — Decouple config, state, and environment

Implement explicit config resolution, optional verified legacy mode, packaged
resource loading, stable user-state derivation, and explicit-only environment file
loading. Preserve registry version 1 and explicit legacy state paths.

Exit gate:

- explicit installed config works from an unrelated cwd with all checkout-related
  environment variables cleared;
- knowledgeHQ compatibility fixture is unchanged;
- two configs have isolated default state;
- existing ledger claim/replay/audit tests pass; and
- no code path reads a project `.env` or scans arbitrary ancestors.

### Change 5 — Select and validate the packaged adapter

Switch default lookup to package resources, remove ambient PATH selection, validate
the handshake before search, and retain the verified checkout fallback for developer
mode. Keep temporary bundle containment and cleanup behavior.

Exit gate:

- installed search/read/context run without the checkout or compiler;
- override/package/checkout selection is deterministic and tested;
- wrong architecture, non-executable, symlink, relative override, timeout, failed
  search, invalid response, and unknown result ID produce bounded errors; and
- there is no SQLite or PATH fallback.

### Change 6 — Implement doctor and capability guards

Add the service health report, synthetic search, state probe, CLI exit behavior, and
central GitHub capability guard. Audit all GitHub and design-asset entry points.

Exit gate:

- healthy installed artifact returns `ok: true` from unrelated cwd;
- each core failure returns `ok: false` and exit code 2;
- missing optional dependencies appear under capabilities without failing core;
- disabled operations make no subprocess/network/OAuth call; and
- stdio integration confirms clean stdout and bounded stderr.

### Change 7 — Documentation and branch acceptance

Update installation/developer docs, configuration fields, adapter protocol, state
behavior, optional capabilities, troubleshooting, and #4/#5/#7 acceptance mapping.
Run the complete branch gate and attach artifact evidence to the pull request.

Exit gate:

- all checks below pass;
- no acceptance criterion is represented only by a mock when a real artifact or
  subprocess test is required;
- issue #8 clearly owns the remaining cross-platform matrix; and
- issue #9 clearly owns publication and live knowledgeHQ migration.

## Test architecture

Keep fast unit tests separate from artifact tests so local iteration stays quick,
while the branch gate always runs both.

| Layer | Coverage |
| --- | --- |
| Rust unit/integration | request limits, strict JSON schema, document-count guard, full-body search, `--info`, build target, bounded errors |
| Python unit | config precedence, state derivation, environment loading, resource selection, handshake parsing, typed failures, redaction, capability guards |
| Service integration | refresh/search/read/context, disabled projects, symlinks, exclusions, stale deletion, ledger compatibility, doctor sections |
| Artifact integration | wheel/sdist contents and tags, clean install, no checkout/compiler, relocated cwd, packaged binary execution |
| MCP subprocess | real stdio initialize/list/search/read/context, protocol-only stdout, bounded stderr, clean shutdown |
| Compatibility | current knowledgeHQ registry structure and explicit state path without private body snapshots |

Required negative cases include:

- missing, relative, symlinked, non-executable, corrupt, wrong-target, and
  protocol-incompatible adapters;
- adapter info/search timeout, nonzero exit, oversized stdout/stderr, malformed JSON,
  duplicate/unknown result IDs, invalid/NaN scores, and result-limit violations;
- missing/malformed registry, traversal roots, disappearing roots, unwritable state,
  two configs sharing a process, and project `.env` traps;
- disabled GitHub/design-vault calls with spies proving zero subprocess/network/OAuth
  interaction; and
- concurrent searches plus interrupted adapter cleanup without deleting the durable
  ledger or another request's temporary bundle.

## Branch acceptance gate

Run these from a clean tree, using Command Line Tools explicitly on macOS only when
the active Xcode selection is broken:

```sh
cargo fmt --check --manifest-path mcp/okf-bridge/Cargo.toml
cargo clippy --locked --manifest-path mcp/okf-bridge/Cargo.toml -- -D warnings
cargo test --locked --manifest-path mcp/okf-bridge/Cargo.toml
uv sync --locked --project mcp
mcp/.venv/bin/python -m unittest discover -s mcp/tests -v
uv build --sdist --wheel --project mcp
git diff --check
```

Add a dedicated installed-artifact script that creates a fresh temporary virtual
environment, installs only the built wheel plus resolved runtime dependencies,
clears `PYTHONPATH` and unrelated `KNOWB_*` variables, changes to an unrelated cwd,
hides Cargo/Git/`gh`, and runs:

1. adapter `--info`;
2. CLI doctor against an explicit synthetic registry;
3. search, read, and context;
4. a real MCP stdio initialize/list/search/read sequence; and
5. archive/content assertions plus cleanup checks.

The real adapter and artifact tests must fail if the binary is absent. Skipping them
is allowed only in the fast developer test command, never in the branch acceptance
or CI artifact job.

## Acceptance traceability

| Issue | Criteria delivered here | Evidence |
| --- | --- | --- |
| #4 | packaged executable, correct native metadata, sdist rebuild, version info, no private contents, deterministic lookup | archive inspection, clean wheel install, real `--info` and search |
| #5 | explicit config outside checkout, legacy knowledgeHQ compatibility, isolated default state, preserved ledger, safe env loading | sanitized installed subprocess tests and legacy database fixtures |
| #7 | executable doctor, typed adapter failures, core/optional capability split, disabled-operation guards, stdout/stderr discipline | synthetic health test, failure matrix, spies, real stdio test |

Issue #4's full multi-platform proof is completed by #8. This branch must implement
target-safe packaging and prove the native developer platform plus CI build mechanics;
it must not claim other platforms as supported before #8 passes them.

## Risks and controls

- **Mis-tagged wheel:** derive or explicitly provide target metadata, validate it
  against the compiled adapter, and inspect `WHEEL` metadata before acceptance.
- **Build hook mutates source tree:** stage generated package data in the build
  directory and track only owned files for cleanup.
- **Private files enter artifacts:** use an allowlist for package/sdist contents and
  test forbidden names and representative secret/state patterns.
- **Config precedence selects the wrong corpus:** explicit arguments/environment are
  terminal decisions; never continue to fallback after an invalid explicit path.
- **State history is lost:** make no schema/path change for registries with explicit
  `state_dir`; test a seeded ledger before and after.
- **Packaged adapter differs from Python expectations:** enforce protocol, revision,
  target, and numeric bounds at handshake.
- **Optional tools become implicit dependencies:** central guards and no-network
  tests prove core isolation.
- **Error output leaks content:** map internal errors to bounded codes/messages and
  test that unique secret markers never appear in stdout/stderr.

## Commit and review structure

Use focused commits matching the seven changes above. Do not combine generated
wheel artifacts or local state with source commits. The pull request should link
#4, #5, and #7, state that #8 owns platform certification and #9 owns release and
migration, and include:

- before/after installation behavior;
- built artifact name, tag, size, and SHA-256;
- wheel/sdist content inspection result;
- branch-gate commands and results;
- compatibility and ledger evidence;
- known unsupported platforms; and
- any acceptance item intentionally deferred to #8 or #9.

## Rollback

The branch must preserve the existing source-checkout launch path as verified legacy
mode until #9 migrates knowledgeHQ. No database migration is planned. Rolling back
therefore means reinstalling or launching the previous connector while continuing
to use the same explicit knowledgeHQ registry and state directory.

Before merging, demonstrate that a database written by the branch can be reopened by
the previous connector for list/read/audit operations. If implementation requires a
database schema change, stop and revise this plan: add an explicit schema version,
SQLite backup/restore test, forward migration, and tested downgrade behavior before
proceeding.

## Definition of done

This branch is complete when #4, #5, and #7 have implementation and evidence for
every criterion owned here; a native platform wheel installs and runs independently;
explicit knowledgeHQ configuration and ledger behavior remain compatible; doctor
proves the packaged adapter with synthetic data; optional capabilities do not block
or leak into local knowledge operation; all branch gates pass; and the remaining
work is cleanly bounded to #6, #8, and #9.
