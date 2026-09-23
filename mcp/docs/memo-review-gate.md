# Memo review and refinement gate

`review_memo` checks whether a memo is ready for a user approval step. It does not
save drafts or approve them. The caller owns memo storage and must show the final
memo, checklist, citations, and digest to the user before recording it.

## Review inputs

The tool accepts a registered `project`, `title`, `memo_kind`, `draft`, `purpose`,
`scope`, `next_actions`, and `open_questions_reviewed`. Memo kinds are `memo`,
`decision`, `plan`, `project_direction`, `brief`, and `research`. `related_paths`
and `external_sources` are optional lists.

The formal checks require:

- an active registered project and a non-empty title;
- a title of at most 256 characters;
- a supported memo kind and draft no larger than 65,536 UTF-8 bytes;
- explicit purpose of at most 2,000 characters and scope of at most 4,000 characters;
- one to twenty concrete next actions, each at most 1,000 characters;
- an explicit `true` value for `open_questions_reviewed`; and
- successful validation of every supplied source reference.

Related paths must be project-relative. Each must resolve to a readable document
under the selected project's configured knowledge allowlist. A valid citation
includes the project, relative path, `knowb://` URI, title, and SHA-256 content
hash. Traversal, symlink escapes, disabled projects, and files outside the
allowlist fail the review and return actionable questions.

External sources must be syntactically valid HTTP or HTTPS URLs without embedded
credentials. The connector does not fetch external pages; their returned citation
records that URL syntax alone was checked.

## Review result and approval

The result status is `needs_refinement` or `ready_for_user_approval`. Both include
a checklist, any source errors, and a SHA-256 `review_signature`. The signature is
calculated from normalized memo fields and validated citations using Unicode NFC,
normalized line endings, trimmed outer whitespace, sorted JSON keys, and compact
JSON encoding. It is deterministic content-bound review evidence, not an identity
signature or a record of user approval.

When a review needs refinement, the caller presents its questions, incorporates
the user's answers, and reviews the edited draft again. When ready, the caller
shows the final memo, checklist, citations, and digest, then waits for explicit
user approval. Only then may the caller record the memo with the approved digest
and citations in its metadata. Any subsequent edit requires a new review and
approval. The connector never returns the draft as a stored artifact and does not
create a GitHub pending action for a review.

## Related GitHub proposal

The connector's `propose_pull_request` / `confirm_pull_request` pair follows the
same durable proposal, short-lived token, idempotency, and audit rules as its
other GitHub writes. The proposal previews the repository, head/base, title/body,
draft state, labels, assignees, and milestone. Confirmation is the only step that
creates the PR or applies that metadata.

The proposal inputs are `repository`, `head`, `base`, `title`, `body`, optional
`draft`, `labels`, `assignees`, `milestone`, and `idempotency_key`. Call
`confirm_pull_request` with the returned token to execute it.
