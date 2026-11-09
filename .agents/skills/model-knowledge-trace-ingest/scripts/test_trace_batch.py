"""Multi-source behavior, exact reconstruction and fail-closed batch outcomes."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from normalize_trace import normalize
import trace_batch as batch


class TraceBatchTests(unittest.TestCase):
    def fixture(self, root, family=False):
        members = []
        for index, role in enumerate(['tool', 'assistant']):
            raw = root / ('raw_' + str(index) + '.jsonl')
            raw.write_text('\n'.join(json.dumps(value) for value in [
                {'role': 'user', 'content': 'SYNTHETIC model framework task ' + str(index)},
                {'role': role, 'content': 'shared payload 汉字\x00\n' * 1500},
                {'role': 'tool', 'content': 'SYNTHETIC_END_' + str(index)},
            ]) + '\n')
            directory = root / ('normalized_' + str(index))
            self.assertTrue(normalize(raw, directory)['ok'])
            members.append({'trace_id': 't' + str(index), 'normalized_dir': str(directory),
                            'source_family': 'same' if family else 'family_' + str(index)})
        source = root / 'input.json'
        source.write_text(json.dumps({'schema_version': batch.LOCAL, 'traces': members}))
        return source, members

    def mined(self, root, prepared):
        manifest = json.loads((prepared / 'manifest.json').read_text())
        work = root / 'work'
        work.mkdir()
        (work / 'DRAFT-c1.md').write_text('SYNTHETIC batch candidate, not a published knowledge card')
        mined = {'schema_version': 'model.trace-mining.v1', 'sources': [s['source'] for s in manifest['sources']],
                 'candidates': [{'candidate_id': 'c1', 'route': 'inference', 'draft_path': 'DRAFT-c1.md',
                                 'sources': [0, 1], 'reproduce_count': 1}]}
        path = work / 'manifest.json'
        path.write_text(json.dumps(mined))
        report = batch.template(prepared)
        for row in report['traces']:
            row.update(disposition='mined', candidate_ids=['c1'])
        report_path = work / 'batch-report.json'
        report_path.write_text(json.dumps(report))
        return path, report_path, mined, report

    def test_windows_cross_sources_and_deduplicate_without_losing_text_or_roles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, members = self.fixture(root)
            result = batch.prepare(source, root / 'batch', packet_bytes=12000, chunk_characters=1300)
            self.assertGreater(result['duplicate_characters'], 0)
            manifest = json.loads((root / 'batch/manifest.json').read_text())
            self.assertTrue(any(len(p['trace_ids']) > 1 for p in manifest['packets']))
            texts, roles = {}, {}
            for index, info in enumerate(manifest['packets'], 1):
                objects = {}  # Each window must resolve independently of earlier contexts.
                self.assertLessEqual(info['bytes'], 12000)
                for item in batch.packet(root / 'batch', index)['records']:
                    key = (item['trace_id'], item['sequence'])
                    if item['kind'] == 'event':
                        roles[key] = item['metadata']['actor']
                        texts[key] = ''
                    else:
                        digest = item['content_sha256']
                        if 'text_parts' in item:
                            self.assertNotIn(digest, objects)
                            objects[digest] = ''.join(item['text_parts'])
                        self.assertEqual(len(texts[key]), item['offset'])
                        texts[key] += objects[digest]
            for member in members:
                for line in (Path(member['normalized_dir']) / 'normalized_trace.jsonl').read_text().splitlines():
                    event = json.loads(line)
                    key = (member['trace_id'], event['sequence'])
                    self.assertEqual(event['actor'], roles[key])
                    self.assertEqual(event['content']['text'], texts[key])
            self.assertNotEqual(roles[('t0', 2)], roles[('t1', 2)])
            page = batch.event(root / 'batch', 't0', 2, 900, 2000)
            self.assertEqual(texts[('t0', 2)][900:2900], ''.join(page['text_parts']))

    def test_cross_trace_candidate_is_one_candidate_and_both_sources_are_accounted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _ = self.fixture(root)
            batch.prepare(source, root / 'batch')
            candidate, report_path, mined, report = self.mined(root, root / 'batch')
            result = batch.check(root / 'batch', report_path, candidate)
            self.assertEqual((2, 1), (result['traces'], result['candidates']))
            self.assertFalse(result['semantic_or_independent_review_pass'])
            for bad in [report['traces'][:1], report['traces'] * 2]:
                value = {**report, 'traces': bad}
                report_path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, 'exactly one'):
                    batch.check(root / 'batch', report_path, candidate)
            report_path.write_text(json.dumps(report))
            mined['candidates'][0]['sources'] = [0]
            candidate.write_text(json.dumps(mined))
            with self.assertRaisesRegex(ValueError, 'membership'):
                batch.check(root / 'batch', report_path, candidate)

    def test_same_family_and_foreign_source_and_draft_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _ = self.fixture(root, family=True)
            batch.prepare(source, root / 'batch')
            path, report, mined, _ = self.mined(root, root / 'batch')
            original = copy.deepcopy(mined)
            mined['candidates'][0]['reproduce_count'] = 2
            path.write_text(json.dumps(mined))
            with self.assertRaisesRegex(ValueError, 'same-family'):
                batch.check(root / 'batch', report, path)
            for field, value in [('raw_source_sha256', '0' * 64), ('normalized_dir', '/outside')]:
                mined = copy.deepcopy(original)
                mined['sources'][0][field] = value
                path.write_text(json.dumps(mined))
                with self.assertRaisesRegex(ValueError, 'foreign'):
                    batch.check(root / 'batch', report, path)
            mined = copy.deepcopy(original)
            mined['sources'].append({'normalized_dir': '/unused-foreign', 'raw_source_sha256': '0' * 64,
                                     'normalized_trace_sha256': '1' * 64})
            path.write_text(json.dumps(mined))
            with self.assertRaisesRegex(ValueError, 'foreign'):
                batch.check(root / 'batch', report, path)
            mined = copy.deepcopy(original)
            mined['candidates'][0]['draft_path'] = '../input.json'
            path.write_text(json.dumps(mined))
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                batch.check(root / 'batch', report, path)

    def test_pending_templates_stale_sources_and_changed_packets_are_not_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, members = self.fixture(root)
            batch.prepare(source, root / 'batch')
            candidate, report, _, complete_report = self.mined(root, root / 'batch')
            report.write_text(json.dumps(batch.template(root / 'batch')))
            with self.assertRaisesRegex(ValueError, 'unprocessed'):
                batch.check(root / 'batch', report, candidate)
            p = next((root / 'batch/packets').glob('*.json'))
            p.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'packet bytes'):
                batch.packet(root / 'batch', 1)
            report.write_text(json.dumps(complete_report))
            with self.assertRaisesRegex(ValueError, 'packet bytes'):
                batch.check(root / 'batch', report, candidate)
            Path(members[0]['normalized_dir'], 'session_manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                batch.check(root / 'batch', report, candidate)

    def test_unfinished_selection_duplicate_sources_and_unsafe_output_fail_before_mining(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, members = self.fixture(root)
            source.write_text(json.dumps({'schema_version': batch.SELECTED,
                'screening': {'complete': False, 'unresolved': 1}, 'traces': members}))
            with self.assertRaisesRegex(ValueError, 'screening'):
                batch.prepare(source, root / 'batch')
            source.write_text(json.dumps({'schema_version': batch.LOCAL, 'traces': [members[0],
                {**members[0], 'trace_id': 'other'}]}))
            with self.assertRaisesRegex(ValueError, 'duplicate normalized'):
                batch.prepare(source, root / 'batch')
            (root / 'link').symlink_to(root / 'destination')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                batch.fresh_output(root / 'link/out')

    def test_raw_batch_normalizes_multiple_members_without_executing_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / 'MUST_NOT_EXECUTE'
            inputs = []
            for index in range(2):
                p = root / ('source_' + str(index) + '.jsonl')
                p.write_text(json.dumps({'role': 'user', 'content': 'synthetic command: touch ' + str(marker)}))
                inputs.append({'trace_id': 't' + str(index), 'path': str(p), 'format': 'auto'})
            source = root / 'raw-input.json'
            source.write_text(json.dumps({'schema_version': batch.LOCAL, 'traces': inputs}))
            result = batch.normalize_batch(source, root / 'normalized')
            prepared = batch.prepare(result['input'], root / 'batch')
            self.assertEqual(2, prepared['traces'])
            self.assertFalse(marker.exists())
            self.assertEqual(0, result['model_calls'])


if __name__ == '__main__':
    unittest.main()
