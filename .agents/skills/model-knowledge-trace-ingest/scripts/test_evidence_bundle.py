"""Reference batches and bounded evidence packets preserve exact multi-source observations."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from evidence_bundle import build
from normalize_trace import normalize
import trace_batch


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.expected, rows = {}, []
        for name in ['a', 'b']:
            raw = self.root / (name + '.jsonl')
            original = [{'role': 'system', 'content': 'SYNTHETIC historical template'},
                        {'role': 'user', 'content': 'SYNTHETIC framework task'},
                        {'role': 'assistant', 'tool_calls': [{'id': 'call', 'function': {
                            'name': 'observe', 'arguments': '{"value": 1}'}}]},
                        {'role': 'tool', 'tool_call_id': 'call', 'content': '汉字\x00\r\n"x' * 1500},
                        {'role': 'tool', 'content': ''}]
            raw.write_text(''.join(json.dumps({'session_id': name, **r}) + '\n' for r in original))
            directory = self.root / ('normalized-' + name)
            normalize(raw, directory)
            rows.append({'trace_id': name, 'normalized_dir': str(directory)})
            self.expected[name] = {e['sequence']: e['content']['text'] for e in map(
                json.loads, (directory / 'normalized_trace.jsonl').read_text().splitlines())}
        self.input = self.root / 'input.json'
        self.input.write_text(json.dumps({'schema_version': trace_batch.LOCAL, 'traces': rows}))
        self.batch = self.root / 'batch'
        trace_batch.prepare(self.input, self.batch, references_only=True)
        self.selection = self.root / 'selection.json'
        self.selection.write_text(json.dumps([{'trace_id': 'a', 'sequences': [4, 5]},
                                              {'trace_id': 'b', 'sequences': [4]}]))

    def tearDown(self):
        self.temp.cleanup()

    def test_no_materialized_store_and_all_selected_characters_survive_page_boundaries(self):
        self.assertFalse((self.batch / 'content.sqlite3').exists())
        result = build(self.batch, self.selection, self.root / 'evidence', max_bytes=4096, context=0)
        manifest = json.loads(Path(result['manifest']).read_text())
        seen = {}
        multi = False
        for page in manifest['pages']:
            raw = (self.root / 'evidence' / page['path']).read_bytes()
            self.assertLessEqual(len(raw), 4096)
            self.assertEqual(page['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertTrue(all(len(line.encode()) < 2000 for line in raw.decode().splitlines()))
            records = json.loads(raw)['records']
            multi |= len(records) > 1
            for r in records:
                key = (r['trace_id'], r['sequence'])
                before = seen.get(key, '')
                self.assertEqual(len(before), r['offset'])
                seen[key] = before + ''.join(r['text_parts'])
        self.assertTrue(multi)
        self.assertEqual({('a', 3), ('a', 4), ('a', 5), ('b', 3), ('b', 4)}, set(seen))
        for (name, n), text in seen.items():
            self.assertEqual(self.expected[name][n], text)
        self.assertEqual([[1, 2]], manifest['sources'][0]['unread_ranges'])
        self.assertTrue(manifest['preparation_is_not_semantic_reading'])

    def test_reference_batches_support_precise_event_reads_and_honest_deferred_reports(self):
        page = trace_batch.event(self.batch, 'a', 4)
        self.assertTrue(''.join(page['text_parts']) in self.expected['a'][4])
        report = trace_batch.template(self.batch)
        for row in report['traces']:
            row.update(disposition='deferred', deferred_stage='unread', reason='not yet read')
        report_path, mined = self.root / 'report.json', self.root / 'mined.json'
        report_path.write_text(json.dumps(report))
        mined.write_text(json.dumps({'schema_version': 'model.trace-mining.v1', 'sources': [], 'candidates': []}))
        result = trace_batch.check(self.batch, report_path, mined)
        self.assertFalse(result['all_targets_resolved'])
        self.assertEqual({'unread': 2}, result['deferred_stages'])
        report['traces'][0]['deferred_stage'] = 'complete'
        report_path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'deferred stage'):
            trace_batch.check(self.batch, report_path, mined)

    def test_tool_pairing_keeps_numeric_and_string_call_identities_distinct(self):
        raw = self.root / 'typed.jsonl'
        raw.write_text(''.join(json.dumps(row) + '\n' for row in [
            {'session_id': 'typed', 'role': 'assistant', 'tool_calls': [
                {'id': 1, 'function': {'name': 'probe', 'arguments': '{}'}}]},
            {'session_id': 'typed', 'role': 'tool', 'tool_call_id': 1, 'content': 'numeric result'},
            {'session_id': 'typed', 'role': 'assistant', 'tool_calls': [
                {'id': '1', 'function': {'name': 'probe', 'arguments': '{}'}}]},
            {'session_id': 'typed', 'role': 'tool', 'tool_call_id': '1', 'content': 'string result'}]))
        directory = self.root / 'typed-normalized'
        normalize(raw, directory)
        selected = self.root / 'typed-input.json'
        selected.write_text(json.dumps({'schema_version': trace_batch.LOCAL, 'traces': [
            {'trace_id': 'typed', 'normalized_dir': str(directory)}]}))
        batch = self.root / 'typed-batch'
        trace_batch.prepare(selected, batch, references_only=True)
        self.selection.write_text(json.dumps([{'trace_id': 'typed', 'sequences': [2]}]))
        output = self.root / 'typed-evidence'
        build(batch, self.selection, output, context=0)
        manifest = json.loads((output / 'evidence.json').read_text())
        self.assertEqual([1, 2], manifest['sources'][0]['included_sequences'])

    def test_changed_sources_foreign_selection_and_output_links_fail_before_writes(self):
        self.selection.write_text(json.dumps([{'trace_id': 'foreign', 'sequences': [1]}]))
        with self.assertRaisesRegex(ValueError, 'foreign'):
            build(self.batch, self.selection, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())
        self.selection.write_text(json.dumps([{'trace_id': 'a', 'sequences': [True]}]))
        with self.assertRaisesRegex(ValueError, 'sequences'):
            build(self.batch, self.selection, self.root / 'bad')
        self.selection.write_text(json.dumps([{'trace_id': 'a', 'sequences': [4]}]))
        (self.root / 'link').symlink_to(self.root / 'outside')
        with self.assertRaisesRegex(ValueError, 'must be new'):
            build(self.batch, self.selection, self.root / 'link')
        source = self.root / 'normalized-a/normalized_trace.jsonl'
        source.write_text(source.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            build(self.batch, self.selection, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())


if __name__ == '__main__':
    unittest.main()
