# Connector engineering policy adoption

Policy version: `2026-10-17.1`.

The owner-directed policy rejects scope inflation, repeated review/repair loops,
unnecessary model calls, token waste and unapproved spending. It requires the
smallest useful behavior, a minimum viable test (MVT), evidence and a stopping
condition. The packaged rules preserve the owner's explicit stance, “BigAI is
BigEvil.” They are engineering instructions, not evidence of provider intent or a
claim to control a model provider's hidden billing system.

## Delivery contract

The private connector implementation is tracked in [KnowledgeHQ PR #61](https://github.com/knowb-ai/knowledgeHQ/pull/61).

- `get_project_context` returns `engineering_policy` containing `version`,
  `sha256` and `content`. The hash covers the exact UTF-8 content returned.
- MCP initialization and the project-work prompt reference that same policy.
  `get_connector_capabilities` and health capabilities expose its version/hash.
  Ordinary search/read results do not repeat the rules.
- New repository scaffolds embed the packaged policy in `AGENTS.md`, retaining
  their passport, client example and validation guide.
- Portable `init` creates `AGENTS.md` only when absent. Existing instructions are
  preserved even with `--force`.
- Existing registered projects receive the policy on their next context request
  after their connector is updated and restarted. Context reads do not rewrite
  project files. A persistent instruction-file update uses that project's reviewed
  change process.

The host must consume the policy under its instruction precedence. Delivery is
not a guarantee of obedience, and the policy grants no access or spending rights.

## Updating a client

After the source change is reviewed and merged, update the connector runtime and
restart its MCP process. KnowledgeHQ's documented clean-main launcher refreshes
its source checkout at startup. Keep the existing registry and state directory.
Verify `get_connector_capabilities.engineering_policy`, then confirm project
context reports the same policy version and hash.

A pinned wheel needs an approved replacement built from the reviewed source.
The immutable public [`mcp-v0.2.0` release](https://github.com/knowb-ai/knowb-ai.github.io/releases/tag/mcp-v0.2.0)
predates these rules. This adoption note publishes no new binary, changes no
existing release asset, and adds no platform-support claim. A new public artifact
remains a separate release operation with its required artifact/platform evidence.

## Validation scope

The source PR records the local checks and exact candidate artifact evidence.
The focused MVT initializes a new fixture, reads an existing fixture through the
installed connector, compares policy identity/content, and verifies existing
files remain unchanged. Scaffolding and stdio checks cover the project-side
contract and initialization/prompt delivery. These checks establish policy
delivery; they do not measure a model's real-world compliance or token savings.

No paid model evaluation, hosted CI workflow or automatic project rewrite is
required to adopt these rules. See the [development handoff](../mcp/docs/development-handoff.md)
for the public release/private runtime boundary.
