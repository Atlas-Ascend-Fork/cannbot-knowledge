"""Equivalent multi-Agent evidence and format-independent failure boundaries."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from model_trace_common import redact_event, sha256_file
from normalize_trace import normalize, verify
import trace_batch


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_source(self, rows, **kwargs):
        source = self.root / 'raw.jsonl'
        source.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        result = normalize(source, self.root / 'out', **kwargs)
        self.assertTrue(result['ok'])
        events = [json.loads(s) for s in (self.root / 'out/normalized_trace.jsonl').read_text().splitlines()]
        manifest = json.loads((self.root / 'out/session_manifest.json').read_text())
        return events, manifest

    def test_same_evidence_across_codex_claude_opencode_and_generic(self):
        cases = {
            'codex': [
                {'type': 'session_meta', 'payload': {'id': 's', 'parent_session_id': 'parent'}},
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                    'content': [{'type': 'input_text', 'text': 'diagnose'}]}},
                {'type': 'response_item', 'payload': {'type': 'function_call', 'name': 'read', 'call_id': 'c',
                    'arguments': '{"path":"config"}'}},
                {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'c', 'output': 'mismatch'}},
            ],
            'claude_code': [
                {'sessionId': 's', 'type': 'user', 'message': {'content': 'diagnose'}},
                {'sessionId': 's', 'type': 'assistant', 'message': {'content': [
                    {'type': 'tool_use', 'name': 'read', 'id': 'c', 'input': {'path': 'config'}}]}},
                {'sessionId': 's', 'type': 'user', 'message': {'content': [
                    {'type': 'tool_result', 'tool_use_id': 'c', 'content': 'mismatch'}]}},
            ],
            'opencode': [
                {'info': {'sessionID': 's', 'role': 'user'}, 'parts': [{'type': 'text', 'text': 'diagnose'}]},
                {'info': {'sessionID': 's', 'role': 'assistant'}, 'parts': [{'type': 'tool', 'tool': 'read',
                    'callID': 'c', 'state': {'status': 'completed', 'input': {'path': 'config'}, 'output': 'mismatch'}}]},
            ],
            'generic': [
                {'session_id': 's', 'role': 'user', 'content': 'diagnose'},
                {'session_id': 's', 'event_type': 'tool_call', 'actor': 'assistant',
                    'tool': {'name': 'read', 'call_id': 'c'}, 'text': '{"path":"config"}'},
                {'session_id': 's', 'role': 'tool', 'tool_call_id': 'c', 'content': 'mismatch'},
            ],
        }
        for label, rows in cases.items():
            with self.subTest(format=label):
                source = self.root / (label + '.jsonl')
                source.write_text(''.join(json.dumps(r) + '\n' for r in rows))
                output = self.root / label
                self.assertTrue(normalize(source, output)['ok'])
                events = [json.loads(s) for s in (output / 'normalized_trace.jsonl').read_text().splitlines()]
                selected = [e for e in events if e['event_type'] != 'session_start']
                self.assertEqual(['user_message', 'tool_call', 'tool_result'], [e['event_type'] for e in selected])
                self.assertEqual(['diagnose', {'path': 'config'}, 'mismatch'], [selected[0]['content']['text'],
                    json.loads(selected[1]['content']['text']), selected[2]['content']['text']])
                self.assertTrue(all(e['session_id'] == 's' for e in selected))
                self.assertEqual(['c', 'c'], [e['tool']['call_id'] for e in selected[1:]])
                if label == 'codex':
                    self.assertTrue(all(e['parent_session_id'] == 'parent' for e in selected))

    def test_generic_mapping_accepts_another_agent_without_source_code_changes(self):
        mapping = {'fields': {'event_type': 'event.kind', 'actor': 'event.who', 'text': 'event.body',
                              'session_id': 'run', 'call_id': 'event.call'},
                   'event_types': {'invoke': 'tool_call', 'return': 'tool_result'}}
        rows = [{'run': 'custom', 'event': {'kind': kind, 'who': actor, 'body': body, 'call': 'c'}}
                for kind, actor, body in [('invoke', 'assistant', 'probe()'), ('return', 'tool', 'observed')]]
        events, manifest = self.run_source(rows, mapping=mapping)
        self.assertEqual(['tool_call', 'tool_result'], [e['event_type'] for e in events])
        self.assertEqual(mapping, manifest['mapping'])
        self.assertEqual(['custom', 'custom'], [e['session_id'] for e in events])

    def test_snapshot_prefixes_preserve_repeated_real_turns_and_explicit_parentage(self):
        turns = [{'role': 'user', 'content': 'SYNTHETIC task'},
                 {'role': 'assistant', 'content': 'SYNTHETIC response'},
                 {'role': 'user', 'content': 'continue'},
                 {'role': 'assistant', 'content': 'SYNTHETIC next'},
                 {'role': 'user', 'content': 'continue'}]
        rows = [{'run': {'id': 's', 'parent': 'p'}, 'capture': {'messages': turns[:n]}}
                for n in [2, 3, 3, 5]]
        mapping = {'layout': 'snapshots', 'messages_path': 'capture.messages',
                   'session_id': 'run.id', 'parent_session_id': 'run.parent'}
        events, manifest = self.run_source(rows, mapping=mapping)
        self.assertEqual([t['content'] for t in turns], [e['content']['text'] for e in events])
        self.assertEqual(2, sum(e['content']['text'] == 'continue' for e in events))
        self.assertTrue(all(e['parent_session_id'] == 'p' for e in events))
        self.assertEqual('snapshots', manifest['layout'])

    def test_snapshot_divergence_and_undecoded_response_are_unknown_not_invented_success(self):
        mapping = {'layout': 'snapshots', 'messages_path': 'history', 'response_path': 'reply'}
        rows = [{'session_id': 's', 'history': [{'role': 'user', 'content': 'original'}],
                 'reply': 'SYNTHETIC opaque event stream'},
                {'session_id': 's', 'history': [{'role': 'user', 'content': 'changed'}]}]
        events, manifest = self.run_source(rows, mapping=mapping)
        self.assertEqual(['user_message', 'unknown', 'unknown'], [e['event_type'] for e in events])
        self.assertIn('SYNTHETIC opaque', events[1]['content']['text'])
        self.assertTrue(any('Non-prefix' in w for w in manifest['warnings']))

    def test_snapshot_response_is_not_repeated_when_next_history_inherits_it(self):
        response = {'role': 'assistant', 'content': 'SYNTHETIC answer'}
        user = {'role': 'user', 'content': 'SYNTHETIC request'}
        events, _ = self.run_source([
            {'session_id': 's', 'messages': [user], 'reply': response},
            {'session_id': 's', 'messages': [user, response]}],
            mapping={'layout': 'snapshots', 'response_path': 'reply'})
        self.assertEqual(['SYNTHETIC request', 'SYNTHETIC answer'], [e['content']['text'] for e in events])

    def test_tool_identity_survives_content_blocks(self):
        events, _ = self.run_source([{'role': 'tool', 'tool_call_id': 'original-call', 'name': 'read',
            'content': [{'type': 'text', 'text': 'exact observed output'}]}])
        self.assertEqual({'name': 'read', 'call_id': 'original-call'}, events[0]['tool'])
        self.assertEqual('tool_result', events[0]['event_type'])

    def test_explicit_tool_failure_is_preserved_as_error(self):
        events, _ = self.run_source([
            {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'c1', 'is_error': True, 'content': 'failed'}]},
            {'role': 'tool', 'tool_call_id': 'c2', 'is_error': True, 'content': [{'type': 'text', 'text': 'failed'}]},
            {'role': 'tool', 'tool_call_id': 'c3', 'is_error': False, 'content': 'observed'}])
        self.assertEqual(['error', 'error', 'tool_result'], [e['event_type'] for e in events])
        self.assertEqual(['c1', 'c2', 'c3'], [e['tool']['call_id'] for e in events])

    def test_explicit_session_persists_but_missing_timestamp_is_not_invented(self):
        events, _ = self.run_source([
            {'type': 'session_meta', 'timestamp': '2026-11-02T00:00:00Z', 'payload': {'id': 's'}},
            {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'actual task'}},
            {'role': 'assistant', 'content': 'unmeasured suggestion'}])
        self.assertEqual(['s'] * 3, [e['session_id'] for e in events])
        self.assertIsNone(events[1]['timestamp'])
        self.assertEqual('user_message', events[1]['event_type'])
        self.assertEqual('assistant_message', events[2]['event_type'])

    def test_malformed_structural_fields_remain_unknown(self):
        rows = [{'type': [], 'opaque': 'preserved'}, {'role': {}, 'text': 'preserved'},
                {'role': 'assistant', 'tool_calls': {'broken': 'preserved'}}]
        events, _ = self.run_source(rows)
        self.assertTrue(all(e['event_type'] == 'unknown' for e in events))
        self.assertEqual(rows, [json.loads(e['content']['text']) for e in events])

    def test_unknown_blocks_and_malformed_records_keep_raw_content(self):
        source = self.root / 'raw.jsonl'
        rows = [{'role': 'assistant', 'content': [{'type': 'image', 'ref': 'evidence.png'},
                  {'type': 'future', 'observation': 'kept'}]}, {'new_schema': {'opaque': 'kept-too'}}]
        broken = '{"unfinished":"SYNTHETIC_TAIL'
        source.write_text(''.join(json.dumps(row) + '\n' for row in rows) + broken)
        normalize(source, self.root / 'out')
        events = [json.loads(s) for s in (self.root / 'out/normalized_trace.jsonl').read_text().splitlines()]
        self.assertEqual(4, len(events))
        self.assertTrue(all(e['event_type'] == 'unknown' for e in events))
        self.assertEqual(rows[0]['content'][0], json.loads(events[0]['content']['text']))
        self.assertEqual(rows[1], json.loads(events[2]['content']['text']))
        self.assertEqual(broken, events[3]['content']['text'])

    def test_no_text_cropping_deduplication_or_execution(self):
        marker = self.root / 'must_not_exist'
        long_text = '汉字\x00\r\n' * 25000 + 'SYNTHETIC_END'
        rows = [{'role': 'assistant', 'tool_calls': [{'id': 'c', 'function': {
            'name': 'bash', 'arguments': json.dumps({'command': 'touch ' + str(marker)})}}]},
                {'role': 'tool', 'tool_call_id': 'c', 'content': long_text},
                {'role': 'tool', 'tool_call_id': 'c', 'content': long_text}]
        events, _ = self.run_source(rows)
        self.assertEqual(3, len(events))
        self.assertEqual(long_text, events[1]['content']['text'])
        self.assertEqual(long_text, events[2]['content']['text'])
        self.assertFalse(marker.exists())

    def test_redaction_is_structured_and_format_independent(self):
        command = 'expect "password:"\nsend "SYNTHETIC_PASSWORD\\r"\n'
        event, count = redact_event({'content': {'text': json.dumps({'command': command,
            'api_key': 'SYNTHETIC_KEY', 'authorization': 'Bearer SYNTHETIC_TOKEN'})}})
        self.assertGreater(count, 0)
        self.assertNotIn('SYNTHETIC_', event['content']['text'])
        self.assertIsInstance(json.loads(event['content']['text'])['command'], str)
        clean, _ = redact_event({'content': {'text': '账号密码：SYNTHETIC_PASS STORAGE_SK=SYNTHETIC_KEY'}})
        self.assertNotIn('SYNTHETIC_', clean['content']['text'])

    def test_hashes_detect_mutation_and_preserve_raw_input(self):
        events, _ = self.run_source([{'role': 'user', 'content': 'original'}])
        raw = self.root / 'raw.jsonl'
        self.assertEqual(sha256_file(raw), events[0]['provenance']['raw_file_sha256'])
        trace = self.root / 'out/normalized_trace.jsonl'
        trace.write_text(trace.read_text().replace('original', 'tampered'))
        with self.assertRaisesRegex(ValueError, 'content hash'):
            verify(self.root / 'out')
        with self.assertRaises(ValueError):
            normalize(raw, self.root / 'out')
        self.assertIn('original', raw.read_text())

    def test_text_transcript_is_one_unknown_instead_of_invented_roles(self):
        source = self.root / 'transcript.md'
        original = '# User\nunknown schema\n# Tool\nobserved?\n'
        source.write_text(original)
        result = normalize(source, self.root / 'out')
        self.assertEqual(1, result['unknown_events'])
        event = json.loads((self.root / 'out/normalized_trace.jsonl').read_text())
        self.assertEqual(original, event['content']['text'])

    def test_unsupported_members_and_symlinks_fail_before_output(self):
        source = self.root / 'raw'
        source.mkdir()
        (source / 'good.json').write_text('{"role":"user","content":"good"}')
        binary = source / 'unsupported.bin'
        binary.write_bytes(b'\x00')
        with self.assertRaises(ValueError):
            normalize(source, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())
        binary.unlink()
        (source / 'link.json').symlink_to(source / 'good.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            normalize(source, self.root / 'out')

    def test_parent_segments_do_not_bypass_knowledge_output_boundary(self):
        source = self.root / 'raw.json'
        source.write_text('{"role":"user","content":"task"}')
        destination = self.root / 'staging/../knowledge/out'
        with patch('normalize_trace.REPOSITORY', self.root):
            with self.assertRaisesRegex(ValueError, 'knowledge'):
                normalize(source, destination)
        with patch.object(trace_batch, 'REPOSITORY', self.root):
            with self.assertRaisesRegex(ValueError, 'knowledge'):
                trace_batch.fresh_output(destination)
        self.assertFalse((self.root / 'knowledge').exists())

    def test_invalid_unicode_remains_visible_and_keeps_distinct_raw_identity(self):
        events, _ = self.run_source([{'role': 'user', 'content': '\udca4'},
                                     {'role': 'user', 'content': '\\udca4'}])
        self.assertEqual('\\udca4', events[0]['content']['text'])
        self.assertEqual(events[0]['content']['text'], events[1]['content']['text'])
        self.assertNotEqual(events[0]['provenance']['raw_sha256'], events[1]['provenance']['raw_sha256'])
        for event in events:
            event['content']['text'].encode('utf-8')

    def test_mixed_agent_batch_normalizes_without_model_calls(self):
        source = self.root / 'batch'
        source.mkdir()
        for label, value in [('a', {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': 'a'}}),
                             ('b', {'type': 'assistant', 'message': {'content': 'b'}}),
                             ('c', {'info': {'role': 'user'}, 'parts': [{'type': 'text', 'text': 'c'}]})]:
            folder = source / label
            folder.mkdir()
            (folder / 'trace.jsonl').write_text(json.dumps(value))
        result = trace_batch.normalize_batch(source, self.root / 'normalized')
        self.assertEqual(3, result['traces'])
        self.assertEqual(0, result['model_calls'])
        prepared = trace_batch.prepare(result['input'], self.root / 'prepared')
        self.assertEqual(3, prepared['traces'])


if __name__ == '__main__':
    unittest.main()
