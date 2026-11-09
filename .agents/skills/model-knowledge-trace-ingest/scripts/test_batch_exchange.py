"""Reading views preserve development evidence; transport cannot invent coverage."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import batch_exchange as exchange
from evidence_bundle import build as evidence_bundle
from normalize_trace import normalize
import trace_batch


class ExchangeTests(unittest.TestCase):
    def fixture(self, root):
        sources = []
        for number in range(2):
            raw = root / ('raw' + str(number) + '.jsonl')
            raw.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in [
                {'role': 'system', 'content': 'SYNTHETIC historical instructions'},
                {'role': 'user', 'content': 'SYNTHETIC framework task 汉字\x00\r\nEND_EVENT\nprogress\rnext'},
                {'role': 'tool', 'content': 'SYNTHETIC observation ' * 4000}]))
            normalized = root / ('normalized' + str(number))
            self.assertTrue(normalize(raw, normalized)['ok'])
            sources.append({'trace_id': 't' + str(number), 'normalized_dir': str(normalized)})
        selected = root / 'selected.json'
        selected.write_text(json.dumps({'schema_version': trace_batch.LOCAL, 'traces': sources}))
        trace_batch.prepare(selected, root / 'batch')
        exchange.reading_view(root / 'batch', root / 'view')
        return json.loads((root / 'view/view.json').read_text())

    def test_contiguous_complete_text_and_explicit_omissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = self.fixture(root)
            body = (root / 'view/reading.txt').read_bytes().decode('utf-8')
            previous = -1
            for source in view['sources']:
                self.assertEqual([1], source['context_only_sequences'])
                self.assertEqual([[2, 3]], source['included_ranges'])
                for row in map(json.loads, (Path(source['source']['normalized_dir']) / 'normalized_trace.jsonl').read_text().splitlines()):
                    if row['sequence'] == 1:
                        self.assertNotIn(row['content']['text'], body)
                        continue
                    position = body.index('\nEVENT ', previous + 1) + 1
                    header_end = body.index('\n', position)
                    header = body[position:header_end]
                    metadata = json.loads(header[len('EVENT '):])
                    for key in ['sequence', 'actor', 'event_type', 'tool', 'timestamp',
                                'session_id', 'parent_session_id']:
                        self.assertEqual(row.get(key), metadata.get(key))
                    expected = '\nTEXT_CHARACTERS ' + str(len(row['content']['text'])) + '\n' + row['content']['text']
                    self.assertTrue(body.startswith(header + expected, position))
                    previous = position
            self.assertLess(view['selected_characters'], view['original_characters'])
            with self.assertRaisesRegex(ValueError, 'exceeds budget'):
                exchange.reading_view(root / 'batch', root / 'too-small', max_bytes=10)
            self.assertFalse((root / 'too-small').exists())

    def bundle(self, root, view):
        report = trace_batch.template(root / 'batch')
        for row in report['traces']:
            row.update(disposition='no_knowledge', reason='SYNTHETIC fixture has no validated mechanism')
        bundle = {'schema_version': 'model.trace-file-bundle.v1',
                  'batch_manifest_sha256': view['batch_manifest_sha256'], 'files': {
            'manifest.json': {'json': {'schema_version': 'model.trace-mining.v1',
                                      'sources': [s['source'] for s in view['sources']], 'candidates': []}},
            'batch-report.json': {'json': report},
            'inference/reconstruction.json': {'json': {'schema_version': 'model.trace-reconstruction.v1',
                'route': 'inference', 'traces': [{'source': s['source'], 'coverage': {'semantic_review_ranges': [[2, 3]]},
                                                'timeline': [], 'facts': []} for s in view['sources']]}}}}
        path = root / 'response.txt'
        path.write_text(json.dumps(bundle))
        return bundle, path

    def test_actual_bundle_expands_without_changing_model_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = self.fixture(root)
            bundle, response = self.bundle(root, view)
            result = exchange.unpack(root / 'view', response, root / 'artifacts')
            self.assertTrue(result['ok'])
            self.assertFalse(result['semantic_or_independent_review_pass'])
            for name, value in bundle['files'].items():
                self.assertEqual(value['json'], json.loads((root / 'artifacts' / name).read_text()))
            with self.assertRaisesRegex(ValueError, 'must be new'):
                exchange.unpack(root / 'view', response, root / 'artifacts')

    def test_bounded_evidence_uses_same_transport_and_binds_all_page_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = self.fixture(root)
            selection = root / 'evidence-selection.json'
            selection.write_text(json.dumps([{'trace_id': s['trace_id'], 'sequences': [2, 3]}
                                              for s in view['sources']]))
            evidence_bundle(root / 'batch', selection, root / 'evidence', context=0)
            bundle, response = self.bundle(root, view)
            self.assertTrue(exchange.unpack(root / 'evidence', response, root / 'artifacts')['ok'])
            self.assertEqual(bundle['files']['manifest.json']['json'],
                             json.loads((root / 'artifacts/manifest.json').read_text()))
            page = root / 'evidence/page_00001.json'
            page.write_text(page.read_text() + ' ')
            with self.assertRaisesRegex(ValueError, 'evidence page changed'):
                exchange.unpack(root / 'evidence', response, root / 'changed')
            self.assertFalse((root / 'changed').exists())

    def test_context_coverage_paths_and_old_binding_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = self.fixture(root)
            bundle, response = self.bundle(root, view)
            bad_values = []
            bad = copy.deepcopy(bundle)
            bad['files']['inference/reconstruction.json']['json']['traces'][0]['coverage']['semantic_review_ranges'] = [[1, 3]]
            bad_values.append(bad)
            bad = copy.deepcopy(bundle)
            bad['files']['../outside.json'] = {'json': {}}
            bad_values.append(bad)
            bad = copy.deepcopy(bundle)
            bad['batch_manifest_sha256'] = '0' * 64
            bad_values.append(bad)
            bad = copy.deepcopy(bundle)
            bad['files']['script.py'] = {'text': 'SYNTHETIC must never run'}
            bad_values.append(bad)
            bad = copy.deepcopy(bundle)
            bad['files']['batch-report.json']['json']['traces'][0].pop('disposition')
            bad_values.append(bad)
            for number, bad in enumerate(bad_values):
                response.write_text(json.dumps(bad))
                output = root / ('rejected' + str(number))
                with self.assertRaises(ValueError):
                    exchange.unpack(root / 'view', response, output)
                self.assertFalse(output.exists())

    def test_invalid_candidate_local_anchor_is_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            view = self.fixture(root)
            bundle, response = self.bundle(root, view)
            mined = bundle['files']['manifest.json']['json']
            mined['candidates'] = [{'candidate_id': 'c1', 'route': 'inference', 'sources': [1],
                'draft_path': 'DRAFT-c1.md', 'claims': [{'text': 'SYNTHETIC claim',
                    'anchors': [{'source': 1, 'sequence': 3}]}]}]
            bundle['files']['DRAFT-c1.md'] = {'text': 'SYNTHETIC draft; never published'}
            row = bundle['files']['batch-report.json']['json']['traces'][1]
            row.update(disposition='mined', reason='SYNTHETIC evidence', candidate_ids=['c1'])
            response.write_text(json.dumps(bundle))
            with self.assertRaisesRegex(ValueError, 'candidate-local'):
                exchange.unpack(root / 'view', response, root / 'invalid-anchor')
            self.assertFalse((root / 'invalid-anchor').exists())
            mined['candidates'][0]['claims'][0]['anchors'][0]['source'] = 0
            response.write_text(json.dumps(bundle))
            exchange.unpack(root / 'view', response, root / 'artifacts')
            result = json.loads((root / 'artifacts/manifest.json').read_text())
            self.assertEqual(mined, result)
            self.assertEqual(bundle['files']['DRAFT-c1.md']['text'], (root / 'artifacts/DRAFT-c1.md').read_text())
            receipt = json.loads((root / 'artifacts/transport-receipt.json').read_text())
            self.assertTrue(receipt['model_authored_content_unchanged'])


if __name__ == '__main__':
    unittest.main()
