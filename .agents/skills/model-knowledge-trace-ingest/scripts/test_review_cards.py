"""A review binds exact staged bytes and cannot approve changed evidence."""

import json
import unittest

import test_model_trace as evidence
from review_cards import REVIEW_CHECKS, subject, verify
from mining_sources import CURATION


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = evidence.EvidenceTests()
        self.fixture.setUp()
        self.fixture.ledger.write_text(json.dumps(self.fixture.data))
        self.frozen = subject(self.fixture.ledger, self.fixture.cards)
        self.receipt = self.fixture.root / 'receipt.json'
        self.data = {'schema_version': 'model.trace-review.v1', 'subject': self.frozen,
                     'reviewer': 'independent-runtime-reviewer', 'attestation': 'agent-runtime-message',
                     'verdict': 'PASS', 'summary': 'Synthetic evidence checked', 'findings': [],
                     'reviewed_at': '2026-11-02T00:00:00Z'}

    def tearDown(self):
        self.fixture.tearDown()

    def check(self):
        self.receipt.write_text(json.dumps(self.data))
        return verify(self.fixture.ledger, self.fixture.cards, self.receipt, 'independent-runtime-reviewer')

    def test_review_accepts_only_unchanged_subject_and_approval_marker_updates(self):
        self.assertTrue(self.check()['ok'])
        entry = self.fixture.data['entries'][0]
        entry['evidence_audit']['result'] = 'pass'
        entry['evidence_audit']['trace_snapshot']['mechanism_artifacts'][0]['verbatim_verified'] = True
        self.fixture.ledger.write_text(json.dumps(self.fixture.data))
        self.assertEqual(self.frozen, subject(self.fixture.ledger, self.fixture.cards))
        self.assertTrue(self.check()['ok'])
        entry['claims'][0]['text'] = 'changed claim'
        self.fixture.ledger.write_text(json.dumps(self.fixture.data))
        with self.assertRaisesRegex(ValueError, 'current staged bytes'):
            self.check()

    def test_changed_card_or_reconstruction_invalidates_review(self):
        card = next(self.fixture.cards.rglob('*.md'))
        original = card.read_bytes()
        card.write_bytes(original + b'\nchanged')
        with self.assertRaisesRegex(ValueError, 'current staged bytes'):
            self.check()
        card.write_bytes(original)
        reconstruction = self.fixture.root / 'reconstruction.json'
        reconstruction.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'reconstruction changed'):
            self.check()

    def test_blockers_or_wrong_sender_do_not_approve(self):
        self.data['findings'] = [{'severity': 'major'}]
        with self.assertRaisesRegex(ValueError, 'findings'):
            self.check()
        self.data['findings'] = []
        self.data['reviewer'] = 'author'
        with self.assertRaisesRegex(ValueError, 'sender'):
            self.check()
        self.data['reviewer'] = 'independent-runtime-reviewer'
        self.data['verdict'] = 'NEEDS_REVISION'
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            self.check()

    def test_unlisted_card_cannot_share_approved_subject(self):
        (self.fixture.cards / 'unexpected.md').write_text('not reviewed')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.check()

    def test_semantic_findings_cannot_be_downgraded_to_minor(self):
        for category in ['evidence', 'api_contract', 'comparison', 'scope', 'validation', 'causality']:
            self.data['findings'] = [{'severity': 'minor', 'category': category,
                                      'issue': 'SYNTHETIC contradiction or unsupported conclusion'}]
            with self.subTest(category=category), self.assertRaisesRegex(ValueError, 'semantic findings'):
                self.check()

    def test_curation_receipt_requires_all_claims_full_units_and_extra_assertion_check(self):
        self.fixture.data['curation_contract'] = CURATION
        self.fixture.ledger.write_text(json.dumps(self.fixture.data))
        self.data['subject'] = subject(self.fixture.ledger, self.fixture.cards)
        with self.assertRaisesRegex(ValueError, 'coverage'):
            self.check()
        row = {'path': 'runtime/config_probe.md', 'claim_ids': ['c1'], 'checked': sorted(REVIEW_CHECKS),
               'complete_artifact_indexes': [0], 'unmapped_assertions': []}
        self.data['coverage'] = [row]
        self.assertTrue(self.check()['ok'])
        row['unmapped_assertions'] = ['SYNTHETIC unsupported restart advice in the description']
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            self.check()
        row['unmapped_assertions'] = []
        row['complete_artifact_indexes'] = []
        with self.assertRaisesRegex(ValueError, 'complete mechanism units'):
            self.check()


if __name__ == '__main__':
    unittest.main()
