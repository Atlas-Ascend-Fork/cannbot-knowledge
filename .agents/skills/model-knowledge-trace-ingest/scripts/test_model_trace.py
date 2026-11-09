"""Behavioral tests; all evidence and credentials below are synthetic fixtures."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from model_trace_common import child, sha256_file
from normalize_trace import normalize
from validate_model_evidence import validate


class PathBoundaryTests(unittest.TestCase):
    def test_traversal_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                child(root, '../outside')
            (root / 'link').symlink_to(root / 'absent')
            with self.assertRaises(ValueError):
                child(root, 'link/file')



class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        normalized = self.root / 'normalized'
        events = []
        for sequence, kind, actor, text in [(1, 'user_message', 'user', 'diagnose'),
                                            (2, 'tool_call', 'assistant', 'inspect_config()'),
                                            (3, 'tool_result', 'tool', 'observed mismatch'),
                                            (4, 'assistant_message', 'assistant', 'interpret observation')]:
            events.append({'schema_version': 'trace.event.v1', 'session_id': 'synthetic', 'sequence': sequence,
                           'timestamp': None, 'actor': actor, 'event_type': kind, 'tool': None,
                           'content': {'text': text}, 'provenance': {'raw_source': 'synthetic.json',
                           'raw_record': sequence, 'raw_sha256': 'a' * 64, 'adapter': 'generic'}})
        self.raw = self.root / 'raw.jsonl'
        self.raw.write_text(''.join(json.dumps(e) + '\n' for e in events))
        normalize(self.raw, normalized)
        raw_hash = json.loads((normalized / 'session_manifest.json').read_text())['source']['sha256']
        self.cards = self.root / 'cards'
        (self.cards / 'runtime').mkdir(parents=True)
        claim = '探针观测可区分配置不一致。'
        sections = '\n\n'.join('## ' + section + '\n\n' + (claim if index == 0 else 'inspect_config()')
                               for index, section in enumerate(['适用场景', '触发与观测', '探针与操作',
                                                                '机制与判别', '验证信号', '适用与失效边界']))
        (self.cards / 'runtime/config_probe.md').write_text('''---
type: Runbook
title: 模型配置观测
description: 合成 fixture 用于验证证据合同，不进入知识正文。
tags: [task.debugging, topic.compilation]
status: draft
sources: []
platforms: [a3]
created_at: '2026-10-29T00:00:00Z'
updated_at: '2026-10-29T00:00:00Z'
---
# 模型配置观测

''' + sections + '\n')
        def anchor(n):
            return [{'source': 0, 'sequence': n}]
        self.data = {'schema_version': 'model.trace-ledger.v1', 'route': 'inference', 'entries': [{
            'candidate_id': 'one', 'status': 'published', 'operation': 'new',
            'target_path': 'runtime/config_probe.md', 'knowledge_form': 'diagnostic_rule', 'reproduce_count': 1,
            'dedup': {'decision': 'create', 'queries': ['config probe']},
            'sources': [{'normalized_dir': str(normalized), 'raw_source_sha256': raw_hash,
                         'normalized_trace_sha256': sha256_file(normalized / 'normalized_trace.jsonl')}],
            'evidence_roles': {key: anchor(n) for key, n in [('trigger', 1), ('probe', 2),
                                                           ('observation', 3), ('discrimination', 4)]},
            'claims': [{'id': 'c1', 'text': claim, 'anchors': anchor(3), 'signals': anchor(3)}],
            'evidence_audit': {'mode': 'trace_snapshot', 'result': 'pending', 'trace_snapshot': {
                'mechanism_artifacts': [{'text': 'inspect_config()', 'anchors': anchor(2),
                                        'claim_ids': ['c1'], 'verbatim_verified': False}]}}}]}
        self.ledger = self.root / 'ledger.json'
        reconstruction = {'schema_version': 'model.trace-reconstruction.v1', 'route': 'inference', 'traces': [{
            'source': self.data['entries'][0]['sources'][0], 'task': {'summary': 'synthetic diagnostic'},
            'environment': {'model': 'unknown'}, 'timeline': [{'event_refs': [1, 2, 3, 4]}],
            'facts': [{'event_refs': [3]}], 'assumptions': [], 'unknowns': ['model'], 'limitations': [],
            'coverage': {'indexed_sequence_range': [1, 4], 'semantic_review_ranges': [[1, 4]]}}]}
        path = self.root / 'reconstruction.json'
        path.write_text(json.dumps(reconstruction))
        self.data['reconstruction_sha256'] = sha256_file(path)

    def tearDown(self):
        self.temp.cleanup()

    def run_validation(self):
        self.ledger.write_text(json.dumps(self.data))
        return validate(self.ledger, self.cards, 'inference')

    def test_valid_evidence_and_semantic_tampering(self):
        self.assertEqual(1, self.run_validation()['accepted'])
        self.data['entries'][0]['claims'][0]['signals'] = [{'source': 0, 'sequence': 4}]
        with self.assertRaisesRegex(ValueError, 'objective'):
            self.run_validation()

    def test_bound_multi_trace_family_and_batch_bytes_are_checked(self):
        original = self.data['entries'][0]['sources'][0]
        other_dir = self.root / 'other'
        other_raw = self.root / 'other.jsonl'
        other_raw.write_text(self.raw.read_text() + '\n')
        normalize(other_raw, other_dir)
        metadata = json.loads((other_dir / 'session_manifest.json').read_text())
        other = {'normalized_dir': str(other_dir), 'raw_source_sha256': metadata['source']['sha256'],
                 'normalized_trace_sha256': sha256_file(other_dir / 'normalized_trace.jsonl')}
        self.data['entries'][0]['sources'].append(other)
        reconstruction_path = self.root / 'reconstruction.json'
        reconstruction = json.loads(reconstruction_path.read_text())
        reconstruction['traces'].append({**copy.deepcopy(reconstruction['traces'][0]), 'source': other})
        reconstruction_path.write_text(json.dumps(reconstruction))
        self.data['reconstruction_sha256'] = sha256_file(reconstruction_path)
        input_dir = self.root / 'input'
        input_dir.mkdir()
        manifest = input_dir / 'manifest.json'
        manifest.write_text(json.dumps({'schema_version': 'model.trace-batch.v1', 'sources': [
            {'source': source, 'source_family': 'same-conversation'} for source in [original, other]]}))
        self.data['batch_manifest'] = {'path': str(manifest), 'sha256': sha256_file(manifest)}
        self.assertEqual(1, self.run_validation()['accepted'])
        self.data['entries'][0]['reproduce_count'] = 2
        with self.assertRaisesRegex(ValueError, 'same-family'):
            self.run_validation()
        self.data['entries'][0]['reproduce_count'] = 1
        manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'batch input manifest changed'):
            self.run_validation()

    def test_changed_normalized_content_and_duplicate_reproduction(self):
        self.data['entries'][0]['sources'][0]['normalized_trace_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'content hash'):
            self.run_validation()
        self.data['entries'][0]['sources'][0]['normalized_trace_sha256'] = sha256_file(self.root / 'normalized/normalized_trace.jsonl')
        self.data['entries'][0]['sources'] *= 2
        self.data['entries'][0]['reproduce_count'] = 2
        with self.assertRaisesRegex(ValueError, 'reproduction'):
            self.run_validation()

    def test_reconstruction_is_bound_and_required(self):
        (self.root / 'reconstruction.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'reconstruction content hash'):
            self.run_validation()

    def test_candidate_manifest_is_bound_and_route_coverage_is_exact(self):
        manifest = self.root / 'manifest.json'
        data = {'schema_version': 'model.trace-mining.v1', 'candidates': [
            {'candidate_id': 'one', 'route': 'inference'},
            {'candidate_id': 'two', 'route': 'inference'},
            {'candidate_id': 'training-one', 'route': 'training'}]}
        manifest.write_text(json.dumps(data))
        self.data['candidates_manifest_sha256'] = sha256_file(manifest)
        self.ledger.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'every input candidate'):
            validate(self.ledger, self.cards, 'inference', candidates_manifest=manifest)
        self.data['entries'][0]['source_candidate_ids'] = ['one', 'two']
        self.ledger.write_text(json.dumps(self.data))
        self.assertEqual(1, validate(self.ledger, self.cards, 'inference', candidates_manifest=manifest)['accepted'])
        self.data['entries'].append({'candidate_id': 'duplicate-two', 'source_candidate_ids': ['two'],
                                    'status': 'rejected', 'reason': 'synthetic fixture'})
        self.ledger.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'exactly once'):
            validate(self.ledger, self.cards, 'inference', candidates_manifest=manifest)

    def test_candidate_manifest_change_invalidates_bound_input(self):
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps({'schema_version': 'model.trace-mining.v1',
                                        'candidates': [{'candidate_id': 'one', 'route': 'inference'}]}))
        self.data['candidates_manifest_sha256'] = sha256_file(manifest)
        self.ledger.write_text(json.dumps(self.data))
        validate(self.ledger, self.cards, 'inference', candidates_manifest=manifest)
        manifest.write_text(manifest.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'manifest hash changed'):
            validate(self.ledger, self.cards, 'inference', candidates_manifest=manifest)

    def test_unsupported_performance_gain_and_mismatched_workload(self):
        entry = self.data['entries'][0]
        entry['claims'][0]['kind'] = 'performance_gain'
        with self.assertRaisesRegex(ValueError, 'paired comparison'):
            self.run_validation()
        sample = {'workload': dict.fromkeys(['model', 'hardware', 'precision', 'input_tokens',
                  'output_tokens', 'batch_or_concurrency', 'parallelism', 'measurement'], 'known'),
                  'signals': [{'source': 0, 'sequence': 3}],
                  'metric': {'name': 'TTFT', 'unit': 'ms', 'aggregation': 'median', 'value': 1}}
        entry['performance_comparison'] = {'baseline': copy.deepcopy(sample), 'candidate': copy.deepcopy(sample)}
        entry['performance_comparison']['candidate']['workload']['input_tokens'] = 200
        with self.assertRaisesRegex(ValueError, 'not comparable'):
            self.run_validation()

    def test_fabricated_artifact_and_path_escape(self):
        entry = self.data['entries'][0]
        entry['evidence_audit']['trace_snapshot']['mechanism_artifacts'][0]['text'] = 'fabricated_code()'
        with self.assertRaisesRegex(ValueError, 'artifact absent'):
            self.run_validation()
        entry['target_path'] = '../config_probe.md'
        with self.assertRaises(ValueError):
            self.run_validation()


if __name__ == '__main__':
    unittest.main()
