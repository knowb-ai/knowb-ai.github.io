# knowledgeHQ migration checklist

This checklist is the private-repository companion to the executable connector's
[P6 release plan](portable-release-migration-plan.md). Apply it in the
knowledgeHQ repository only after the release candidate and rollback gates pass.

1. Record the current client command, connector version, registry checksum, and
   resolved project/allowlist fingerprint.
2. Stop the running MCP process and back up
   `.knowb-state/org-index.sqlite` with `backup_sqlite.py`; verify integrity,
   schema, and pending/audit row counts.
3. Install the exact approved wheel in a fresh environment. Keep the registry at
   `.knowb/knowb-ai-portfolio.yml`; do not copy it into the public package.
4. Generate the client JSON with:

   ```sh
   knowb-org --config /absolute/path/to/knowledgeHQ/.knowb/knowb-ai-portfolio.yml \
     client-config --output /absolute/path/to/knowledgeHQ/mcp/knowb-ai-portfolio.client.json \
     --server-name knowb-ai-portfolio --force
   ```

5. Review the JSON, then apply it as a separate approved knowledgeHQ change.
   Confirm it contains only the installed command, absolute registry path, and
   `KNOWB_ORG_CONFIG`.
6. Launch the exact stdio subprocess and run `doctor`, refresh, search, read,
   context, and audit-log checks against the same representative documents used
   in the pre-migration record.
7. Compare project IDs, enabled/disabled state, roots, excludes, citations, and
   ledger fingerprints. Investigate every difference before continuing.
8. Rehearse rollback in an isolated environment with the preserved prior command
   and SQLite backup. Keep both the old client file and backup until the release
   owner closes the recovery gate.

Do not publish registry contents, credentials, state databases, or document bodies
in a release artifact or public repository. Do not silently restart a running
client, provision credentials, or delete the old state.
