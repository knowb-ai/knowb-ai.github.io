"""Governed pull-request proposal and confirmation tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from knowb_org_index.github_ops import GitHubError
from knowb_org_index.server import _confirm_kind
from knowb_org_index.service import OrgIndexService
from support import isolated_registry


class PullRequestProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.service = OrgIndexService(isolated_registry(self.root))
        self.github = self.service.github

    def propose(self, **changes):
        arguments = {
            "repository": "knowb-ai/example",
            "head": "codex/memo-review-gate",
            "base": "main",
            "title": "Add formal memo review",
            "body": "## Problem\n\nA formal memo review gate is missing.",
            "draft": False,
            "labels": ["type/feature", "area/mcp"],
            "assignees": ["valiantone"],
            "milestone": "Memo review and refinement gate",
            "idempotency_key": "test-pr-create",
        }
        arguments.update(changes)
        return self.github.propose_pull_request(**arguments)

    def test_proposal_previews_all_fields_without_mutation_then_confirms_once(self):
        run = Mock(return_value="https://github.com/knowb-ai/example/pull/18")
        self.github._run = run
        proposal = self.propose()

        self.assertEqual(proposal["status"], "pending")
        self.assertEqual(proposal["kind"], "pull_request_create")
        self.assertTrue(proposal["preview"]["requires_confirmation"])
        for field in ("repository", "head", "base", "title", "body", "draft", "labels", "assignees", "milestone"):
            self.assertIn(field, proposal["preview"])
        run.assert_not_called()

        completed = self.github.confirm(proposal["token"])
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["result"]["url"], "https://github.com/knowb-ai/example/pull/18")
        args = run.call_args.args[0]
        for expected in (
            "pr", "create", "--repo", "knowb-ai/example", "--head", "codex/memo-review-gate",
            "--base", "main", "--title", "Add formal memo review", "--label", "type/feature",
            "--label", "area/mcp", "--assignee", "valiantone", "--milestone",
            "Memo review and refinement gate",
        ):
            self.assertIn(expected, args)
        self.assertEqual(run.call_args.kwargs["input_text"], proposal["payload"]["body"])

        replay = self.github.confirm(proposal["token"])
        self.assertTrue(replay["idempotent_replay"])
        run.assert_called_once()
        self.assertIn("completed", {item["event"] for item in self.service.index.audit_log()})

    def test_draft_flag_and_idempotent_proposal(self):
        first = self.propose(draft=True)
        second = self.propose(draft=True)
        self.assertEqual(first["token"], second["token"])
        self.assertTrue(first["preview"]["draft"])

    def test_invalid_refs_and_metadata_are_rejected(self):
        for changes in (
            {"head": "--help"},
            {"head": "feature/../main"},
            {"base": "user:main"},
            {"head": "main", "base": "main"},
            {"labels": [""]},
        ):
            with self.subTest(changes=changes), self.assertRaises(GitHubError):
                self.propose(**changes, idempotency_key=None)

    def test_confirmation_failure_is_audited_and_expired_token_does_not_execute(self):
        failed = self.propose(idempotency_key="failure")
        self.github._run = Mock(side_effect=GitHubError("remote unavailable"))
        with self.assertRaisesRegex(GitHubError, "Confirmed action failed"):
            self.github.confirm(failed["token"])
        self.assertIn("failed", {item["event"] for item in self.service.index.audit_log()})

        expired = self.propose(idempotency_key="expired")
        with self.service.index._connect() as connection:
            connection.execute("UPDATE pending_actions SET expires_at = 0 WHERE token = ?", (expired["token"],))
        self.github._run.reset_mock()
        with self.assertRaisesRegex(GitHubError, "expired"):
            self.github.confirm(expired["token"])
        self.github._run.assert_not_called()
        self.assertIn("expired", {item["event"] for item in self.service.index.audit_log()})

    def test_confirmation_rejects_a_token_for_another_mutation_kind(self):
        issue = self.github.propose_ticket_create(repository="knowb-ai/example", title="Issue")
        self.github._run = Mock(side_effect=AssertionError("wrong-kind token must not execute"))
        with self.assertRaisesRegex(ValueError, "not pull_request_create"):
            _confirm_kind(self.service, issue["token"], "pull_request_create")
        self.github._run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
