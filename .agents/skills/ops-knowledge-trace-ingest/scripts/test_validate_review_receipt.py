#!/usr/bin/env python3

import json
from pathlib import Path
import tempfile
import unittest

from validate_review_receipt import build_subject, validate_receipt


class ReviewReceiptTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "ledger.json"
        self.cards = self.root / "cards"
        self.cards.mkdir()
        self.ledger.write_text(
            '{"entries":[{"status":"published","target_slug":"card","target_path":"card.md"}]}',
            encoding="utf-8",
        )
        (self.cards / "card.md").write_text("# Card\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def _receipt(self, **changes):
        subject = build_subject(self.ledger, self.cards)
        receipt = {
            **subject,
            "verdict": "PASS",
            "findings": [],
            "summary": "independent review passed",
            "reviewer": "subagent:test-reviewer",
            "attestation": "agent-runtime-message",
            "reviewed_at": "2026-08-28T08:00:00Z",
        }
        receipt.update(changes)
        path = self.root / "review-receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return path

    def test_pass_receipt_binds_current_bytes(self):
        result = validate_receipt(self.ledger, self.cards, self._receipt())
        self.assertTrue(result["ok"], result["errors"])

    def test_card_mutation_invalidates_old_pass(self):
        receipt = self._receipt()
        (self.cards / "card.md").write_text("# Changed\n", encoding="utf-8")
        result = validate_receipt(self.ledger, self.cards, receipt)
        self.assertFalse(result["ok"])
        self.assertIn("receipt subject_sha256 does not match current subject", result["errors"])

    def test_reviewer_approval_flags_do_not_invalidate_pass(self):
        pending = {
            "entries": [
                {
                    "status": "published",
                    "target_slug": "card",
                    "target_path": "card.md",
                    "evidence_audit": {
                        "result": "pending",
                        "trace_snapshot": {
                            "mechanism_artifacts": [
                                {"verbatim_verified": False}
                            ]
                        },
                    },
                }
            ]
        }
        self.ledger.write_text(json.dumps(pending), encoding="utf-8")
        receipt = self._receipt()
        pending["entries"][0]["evidence_audit"]["result"] = "pass"
        pending["entries"][0]["evidence_audit"]["trace_snapshot"][
            "mechanism_artifacts"
        ][0]["verbatim_verified"] = True
        self.ledger.write_text(json.dumps(pending), encoding="utf-8")
        result = validate_receipt(self.ledger, self.cards, receipt)
        self.assertTrue(result["ok"], result["errors"])

    def test_curator_decision_mutation_still_invalidates_pass(self):
        self.ledger.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "status": "published",
                            "target_slug": "card",
                            "target_path": "card.md",
                            "reason": "first",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        receipt = self._receipt()
        self.ledger.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "status": "published",
                            "target_slug": "card",
                            "target_path": "card.md",
                            "reason": "changed",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        result = validate_receipt(self.ledger, self.cards, receipt)
        self.assertFalse(result["ok"])
        self.assertIn("receipt subject_sha256 does not match current subject", result["errors"])

    def test_pass_cannot_contain_major_finding(self):
        finding = {
            "severity": "major",
            "card": "card",
            "issue": "issue",
            "location": "body",
            "suggestion": "fix it",
        }
        result = validate_receipt(
            self.ledger,
            self.cards,
            self._receipt(findings=[finding]),
        )
        self.assertFalse(result["ok"])
        self.assertIn("PASS receipt contains blocker or major findings", result["errors"])

    def test_staged_targets_must_match_ledger(self):
        self.ledger.write_text(
            '{"entries":[{"status":"published","target_slug":"other","target_path":"other.md"}]}',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "staged card targets do not match ledger"):
            build_subject(self.ledger, self.cards)


if __name__ == "__main__":
    unittest.main()
