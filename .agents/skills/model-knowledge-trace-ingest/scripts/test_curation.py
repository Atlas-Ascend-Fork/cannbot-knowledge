"""Candidate-to-ledger information loss and misleading publication must fail closed."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

from curate_candidates import promote
from mining_sources import preserve_candidate
from model_trace_common import sha256_file
from review_cards import inventory, subject
import test_model_trace as evidence
from validate_model_evidence import validate
import validate_model_evidence as validator


class CurationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = evidence.EvidenceTests()
        self.fixture.setUp()
        self.root, self.cards = self.fixture.root, self.fixture.cards
        old = self.fixture.data['entries'][0]
        self.candidate = {key: copy.deepcopy(old[key]) for key in
                          ['candidate_id', 'knowledge_form', 'sources', 'evidence_roles', 'claims']}
        self.candidate.update(route='inference', draft_path='DRAFT-runtime-1.md',
                              mechanism_artifacts=copy.deepcopy(old['evidence_audit']['trace_snapshot']['mechanism_artifacts']))
        self.manifest = {'schema_version': 'model.trace-mining.v1', 'sources': old['sources'],
                         'candidates': [self.candidate]}
        self.decision = {'candidate_id': 'one', 'status': 'published', 'operation': 'new',
                         'target_path': 'runtime/config_probe.md', 'dedup': old['dedup'], 'reproduce_count': 1,
                         'scope_evidence': {'summary': 'SYNTHETIC framework diagnostic',
                                            'anchors': [{'source': 0, 'sequence': 1}, {'source': 0, 'sequence': 3}]},
                         'validation_scope': ['source_read']}
        self.input = self.root / 'mine.json'
        self.decisions = self.root / 'decisions.json'
        self.ledger = self.root / 'promoted.json'

    def tearDown(self):
        self.fixture.tearDown()

    def stage(self):
        self.input.write_text(json.dumps(self.manifest))
        self.decisions.write_text(json.dumps([self.decision]))
        promote(self.input, self.decisions, self.root / 'reconstruction.json', self.ledger, 'inference')
        return json.loads(self.ledger.read_text())

    def check(self, data):
        self.ledger.write_text(json.dumps(data))
        return validate(self.ledger, self.cards, 'inference', candidates_manifest=self.input)

    def test_private_information_cannot_be_frozen_or_validated(self):
        self.stage()
        card = next(self.cards.rglob('*.md'))
        original = card.read_text()
        for leak in ['cd /home/synthetic-person/private-project', '见候选 c1']:
            card.write_text(original + '\n```sh\n' + leak + '\n```\n')
            with self.subTest(leak=leak):
                with self.assertRaisesRegex(ValueError, 'publication audit failed'):
                    validate(self.ledger, self.cards, 'inference', candidates_manifest=self.input)
                with self.assertRaisesRegex(ValueError, 'publication audit failed'):
                    subject(self.ledger, self.cards)

    def test_scope_requires_observed_relation_not_only_user_wording(self):
        self.decision['scope_evidence']['anchors'] = [{'source': 0, 'sequence': 1}]
        data = self.stage()
        with self.assertRaisesRegex(ValueError, 'observed integration'):
            self.check(data)

    def performance(self):
        claim = self.candidate['claims'][0]
        claim.update(kind='performance_gain', confidence='SYNTHETIC extra metadata')
        sample = {'workload': dict.fromkeys(['model', 'hardware', 'precision', 'input_tokens', 'output_tokens',
                                            'batch_or_concurrency', 'parallelism', 'measurement'], 'known'),
                  'metric': {'name': 'latency', 'unit': 'ms', 'aggregation': 'median', 'value': 2},
                  'signals': [{'source': 0, 'sequence': 3}]}
        self.candidate['performance_comparison'] = {'baseline': copy.deepcopy(sample), 'candidate': sample}

    def test_promotion_preserves_full_comparison_claim_metadata_and_source_indices(self):
        self.performance()
        self.candidate['sources'] = [0]
        original = copy.deepcopy(self.manifest)
        data = self.stage()
        self.assertEqual(self.candidate['claims'], data['entries'][0]['claims'])
        self.assertEqual(self.candidate['performance_comparison'], data['entries'][0]['performance_comparison'])
        self.assertEqual(original, self.manifest)
        self.assertTrue(self.check(data)['ok'])
        for change in ['kind', 'comparison']:
            bad = copy.deepcopy(data)
            if change == 'kind':
                bad['entries'][0]['claims'][0].pop('kind')
            else:
                bad['entries'][0].pop('performance_comparison')
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'changed or lost'):
                self.check(bad)

    def test_ledger_only_claim_deletion_and_stale_title_are_rejected(self):
        extra = copy.deepcopy(self.candidate['claims'][0])
        extra.update(id='c2', text='SYNTHETIC unsupported conclusion')
        self.candidate['claims'].append(extra)
        card = self.cards / 'runtime/config_probe.md'
        original = card.read_text()
        card.write_text(original + '\n' + extra['text'])
        data = self.stage()
        data['entries'][0]['claims'].pop()
        with self.assertRaisesRegex(ValueError, 'adoption or explicit omission'):
            self.check(data)
        data['entries'][0]['claim_dispositions'] = [
            {'candidate_id': 'one', 'claim_id': 'c2', 'action': 'omitted', 'reason': 'no supporting run'}]
        with self.assertRaisesRegex(ValueError, 'omitted claim remains'):
            self.check(data)
        card.write_text(original.replace('title: 模型配置观测', 'title: ' + extra['text']))
        with self.assertRaisesRegex(ValueError, 'title, description or body'):
            self.check(data)
        card.write_text(original)
        self.assertTrue(self.check(data)['ok'])

    def test_omission_is_explicit_and_all_omitted_requires_deferral(self):
        decision = copy.deepcopy(self.decision)
        decision['omit_claims'] = [{'claim_id': 'c1', 'reason': 'not verified'}]
        with self.assertRaisesRegex(ValueError, 'all claims omitted'):
            preserve_candidate(self.candidate, self.manifest, decision)
        decision.update(status='deferred', reason='missing objective evidence')
        result = preserve_candidate(self.candidate, self.manifest, decision)
        self.assertEqual('deferred', result['status'])
        self.assertNotIn('claims', result)

    def test_a_verbatim_substring_is_not_a_replacement_for_the_original_unit(self):
        data = self.stage()
        artifact = data['entries'][0]['evidence_audit']['trace_snapshot']['mechanism_artifacts'][0]
        artifact['text'] = 'inspect_config'
        with self.assertRaisesRegex(ValueError, 'complete mining mechanism'):
            self.check(data)

    def test_merged_comparisons_keep_member_identity_after_source_remap(self):
        self.performance()
        original = self.candidate['sources'][0]
        other = {**original, 'normalized_dir': str(self.root / 'normalized_copy')}
        shutil.copytree(original['normalized_dir'], other['normalized_dir'])
        second = copy.deepcopy(self.candidate)
        second.update(candidate_id='two', sources=[other])
        self.manifest['candidates'].append(second)
        reconstruction = self.root / 'reconstruction.json'
        content = json.loads(reconstruction.read_text())
        content['traces'].append({**copy.deepcopy(content['traces'][0]), 'source': other})
        reconstruction.write_text(json.dumps(content))
        entry = preserve_candidate(self.candidate, self.manifest, self.decision)
        entry.update(source_candidate_ids=['one', 'two'], sources=[other, original])
        first_claim = entry['claims'][0]
        first_claim.update(source_claims=[{'candidate_id': 'one', 'claim_id': 'c1'}])
        for key in ['anchors', 'signals']:
            for anchor in first_claim[key]:
                anchor['source'] = 1
        second_claim = copy.deepcopy(first_claim)
        second_claim.update(id='c2', source_claims=[{'candidate_id': 'two', 'claim_id': 'c1'}])
        for key in ['anchors', 'signals']:
            for anchor in second_claim[key]:
                anchor['source'] = 0
        entry['claims'].append(second_claim)
        artifacts = entry['evidence_audit']['trace_snapshot']['mechanism_artifacts']
        artifacts.append(copy.deepcopy(artifacts[0]))
        artifacts[0]['anchors'][0]['source'] = 1
        artifacts[1]['claim_ids'] = ['c2']
        entry['performance_comparisons'] = {'one': entry.pop('performance_comparison'),
                                            'two': copy.deepcopy(second['performance_comparison'])}
        for sample in entry['performance_comparisons']['one'].values():
            sample['signals'][0]['source'] = 1
        self.input.write_text(json.dumps(self.manifest))
        data = {'schema_version': 'model.trace-ledger.v1', 'curation_contract': 'model.trace-curation.v1',
                'route': 'inference', 'candidates_manifest_sha256': sha256_file(self.input),
                'reconstruction_sha256': sha256_file(reconstruction), 'entries': [entry]}
        self.assertTrue(self.check(data)['ok'])
        # An internally invalid second pair is rejected even if preserved exactly from mining.
        second['performance_comparison']['candidate']['metric']['unit'] = 'seconds'
        entry['performance_comparisons']['two'] = copy.deepcopy(second['performance_comparison'])
        self.input.write_text(json.dumps(self.manifest))
        data['candidates_manifest_sha256'] = sha256_file(self.input)
        with self.assertRaisesRegex(ValueError, 'metric definitions differ'):
            self.check(data)

    def test_repeated_source_is_cached_but_mid_validation_changes_fail(self):
        data = copy.deepcopy(self.fixture.data)
        second = copy.deepcopy(data['entries'][0])
        second.update(candidate_id='two', target_path='runtime/second.md')
        (self.cards / second['target_path']).write_bytes((self.cards / 'runtime/config_probe.md').read_bytes())
        data['entries'].append(second)
        self.ledger.write_text(json.dumps(data))
        with patch.object(validator, 'verify', wraps=validator.verify) as verify:
            self.assertEqual(2, validate(self.ledger, self.cards, 'inference')['accepted'])
            self.assertEqual(1, verify.call_count)
        real = validator.event_texts
        def changing_source(event):
            result = real(event)
            path = self.root / 'normalized/session_manifest.json'
            path.write_text(path.read_text() + '\n')
            return result
        with patch.object(validator, 'event_texts', side_effect=changing_source):
            with self.assertRaisesRegex(ValueError, 'changed during validation'):
                validate(self.ledger, self.cards, 'inference')

    def test_every_independent_candidate_error_is_reported_together(self):
        data = copy.deepcopy(self.fixture.data)
        first = data['entries'][0]
        second = copy.deepcopy(first)
        second.update(candidate_id='two', target_path='runtime/second.md')
        (self.cards / second['target_path']).write_bytes((self.cards / first['target_path']).read_bytes())
        first['claims'][0]['signals'] = [{'source': 0, 'sequence': 4}]
        second['knowledge_form'] = 'not-a-form'
        data['entries'].append(second)
        self.ledger.write_text(json.dumps(data))
        result = validate(self.ledger, self.cards, 'inference', collect_errors=True)
        self.assertFalse(result['ok'])
        self.assertEqual({'one', 'two'}, {x['candidate_id'] for x in result['errors']})

    def test_cli_creates_complete_report_and_bounded_summary(self):
        data = copy.deepcopy(self.fixture.data)
        data['entries'][0]['knowledge_form'] = 'not-a-form'
        for number in range(25):
            data['entries'].append({'candidate_id': 'bad_' + str(number), 'status': 'deferred'})
        self.ledger.write_text(json.dumps(data))
        report = self.root / 'validation.json'
        command = [sys.executable, str(Path(validator.__file__)), str(self.ledger), str(self.cards),
                   '--route', 'inference', '--report', str(report)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual(26, json.loads(result.stdout)['errors_count'])
        self.assertLess(len(result.stdout), 500)
        original = report.read_bytes()
        self.assertEqual(26, len(json.loads(original)['errors']))
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertIn('must be new', result.stdout)
        self.assertEqual(original, report.read_bytes())

    def test_promotion_cannot_overwrite_follow_links_or_write_in_sources(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, 'must be new'):
            promote(self.input, self.decisions, self.root / 'reconstruction.json', self.ledger, 'inference')
        self.ledger.unlink()
        other = self.root / 'outside.json'
        other.write_text('SYNTHETIC untouched')
        self.ledger.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            promote(self.input, self.decisions, self.root / 'reconstruction.json', self.ledger, 'inference')
        self.assertEqual('SYNTHETIC untouched', other.read_text())
        # Deferred entries must not weaken the immutable source boundary.
        self.decision.update(status='deferred', reason='SYNTHETIC missing evidence')
        self.decisions.write_text(json.dumps([self.decision]))
        normalized = self.root / 'normalized'
        reconstruction = normalized / 'reconstruction.json'
        shutil.copyfile(self.root / 'reconstruction.json', reconstruction)
        with self.assertRaisesRegex(ValueError, 'inside normalized sources'):
            promote(self.input, self.decisions, reconstruction, normalized / 'ledger.json', 'inference')
        self.assertFalse((normalized / 'ledger.json').exists())

    def test_published_inventory_excludes_unrelated_cards_and_checks_actual_bytes(self):
        self.stage()
        relative = 'knowledge/model/inference/runbooks/runtime/config_probe.md'
        published = self.root / 'repository' / relative
        published.parent.mkdir(parents=True)
        published.write_bytes((self.cards / 'runtime/config_probe.md').read_bytes())
        paths = self.root / 'changes.json'
        paths.write_text(json.dumps([relative, 'logs/2026-11-04.md']))
        self.assertTrue(inventory(self.ledger, self.cards, paths, self.root / 'repository')['ok'])
        paths.write_text(json.dumps([relative, relative.replace('config_probe', 'unrelated')]))
        with self.assertRaisesRegex(ValueError, 'accepted inventory'):
            inventory(self.ledger, self.cards, paths, self.root / 'repository')
        paths.write_text(json.dumps([relative]))
        published.write_text('different published content')
        with self.assertRaisesRegex(ValueError, 'published card bytes'):
            inventory(self.ledger, self.cards, paths, self.root / 'repository')


if __name__ == '__main__':
    unittest.main()
