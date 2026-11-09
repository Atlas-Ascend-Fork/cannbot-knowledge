"""Synthetic outcomes, ancestry, and privacy regression boundaries."""

import json
from pathlib import Path
import tempfile
import unittest

from audit_publication import audit
from batch_exchange import reading_view
from normalize_trace import normalize
from read_trace import read_event
from trace_batch import prepare
from trace_adapters import Adapter
from trace_privacy import Redactor, publication_findings, require_publication_clean


class OutcomeTests(unittest.TestCase):
    def test_custom_export_maps_nested_execution_metadata(self):
        adapter = Adapter('custom', {'fields': {'event_type': 'kind', 'actor': 'who', 'text': 'body',
                                               'exit_code': 'execution.returncode',
                                               'truncated': 'execution.cut'}})
        event = list(adapter.convert({'kind': 'tool_result', 'who': 'tool', 'body': 'PASS',
                                      'execution': {'returncode': 1, 'cut': False}}))[0]
        self.assertEqual('error', event['event_type'])
        self.assertEqual(1, event['outcome']['exit_code'])
        self.assertFalse(event['outcome']['output_truncated'])

    def result(self, state):
        return list(Adapter('s').convert({'info': {'role': 'assistant'}, 'parts': [
            {'type': 'tool', 'tool': 'shell', 'state': state}]}))[-1]

    def test_completed_nonzero_is_failure_even_when_stdout_says_pass(self):
        event = self.result({'status': 'completed', 'input': {}, 'output': 'PASS',
                             'metadata': {'exit': 1, 'password': 'synthetic-secret'}})
        self.assertEqual('error', event['event_type'])
        self.assertTrue(event['outcome']['failed'])
        self.assertEqual(1, event['outcome']['exit_code'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / 'raw.json'
            raw.write_text(json.dumps(event))
            normalize(raw, root / 'normalized')
            page = read_event(root / 'normalized', 1)
            self.assertEqual(1, page['outcome']['exit_code'])
            self.assertNotIn('synthetic-secret', json.dumps(page))
            self.assertEqual('synthetic-secret', json.loads(raw.read_text())['result_metadata']['metadata']['password'])
            source = root / 'input.json'
            source.write_text(json.dumps({'schema_version': 'model.trace-local-batch.v1', 'traces': [
                {'trace_id': 'synthetic', 'normalized_dir': str(root / 'normalized')}]}))
            prepare(source, root / 'batch', references_only=True)
            reading_view(root / 'batch', root / 'view')
            rendered = (root / 'view/reading.txt').read_text()
            self.assertIn('"exit_code": 1', rendered)
            self.assertIn('"failed": true', rendered)
            self.assertNotIn('synthetic-secret', rendered)

    def test_truncated_output_is_limited_and_success_is_unqualified(self):
        truncated = self.result({'status': 'completed', 'input': {}, 'output': 'partial',
                                 'metadata': {'exit': 0, 'truncated': True, 'saved': '/home/fake/log'}})
        self.assertIn('tool_output_truncated', truncated['limitations'])
        self.assertTrue(truncated['outcome']['output_truncated'])
        normal = self.result({'status': 'completed', 'input': {}, 'output': 'done',
                              'metadata': {'exit': 0, 'truncated': False}})
        self.assertEqual('tool_result', normal['event_type'])
        self.assertNotIn('limitations', normal)
        self.assertEqual(0, normal['outcome']['exit_code'])

    def test_unknown_or_malformed_status_retains_evidence(self):
        for status in ['waiting-for-retry', ['completed']]:
            with self.subTest(status=status):
                item = self.result({'status': status, 'input': {}, 'output': 'uncertain'})
                self.assertEqual('unknown', item['event_type'])
                self.assertIn('unrecognized_tool_status', item['limitations'])
                self.assertEqual(status, item['result_metadata']['status'])

    def test_message_parent_is_not_a_session_parent(self):
        adapter = Adapter('default')
        row = {'info': {'id': 'm2', 'sessionID': 'child', 'parentID': 'm1', 'role': 'assistant'},
               'parts': [{'type': 'text', 'text': 'synthetic'}]}
        item = list(adapter.convert(row))[0]
        self.assertIsNone(item['parent_session_id'])
        self.assertEqual('m1', item['parent_message_id'])
        self.assertEqual('m2', item['message_id'])
        list(adapter.convert({'type': 'session.created', 'properties': {'info': {'id': 'child', 'parentID': 'parent'}}}))
        item = list(adapter.convert(row))[0]
        self.assertEqual('parent', item['parent_session_id'])
        self.assertEqual('m1', item['parent_message_id'])
        row['parentSessionID'] = 'explicit'
        self.assertEqual('explicit', list(adapter.convert(row))[0]['parent_session_id'])


class PrivacyTests(unittest.TestCase):
    def test_nested_commands_and_metadata_redact_without_changing_raw(self):
        data = {'arguments': json.dumps({'cwd': '/home/synthetic-user/project',
                'cmd': 'cd /home/synthetic-user/project && ssh fake@172.18.2.4',
                'password': 'synthetic-secret'}), 'metadata': {'saved': '/tmp/private-log',
                'email': 'person@example.org'}, 'ipv6': 'fd12::1234',
                'windows': r'C:\Users\synthetic-user\project\file.py'}
        original = json.dumps(data)
        result = Redactor().clean(data)
        cleaned = json.dumps(result)
        for private in ['synthetic-user', '172.18.2.4', 'synthetic-secret', '/tmp/private-log', 'person@example.org', 'fd12::1234']:
            self.assertNotIn(private, cleaned)
        self.assertEqual(original, json.dumps(data))
        self.assertEqual(result, Redactor().clean(result))

    def test_portable_aliases_preserve_relative_paths_and_distinct_identity(self):
        redactor = Redactor({'path_aliases': [{'prefix': '/home/fake/project', 'replacement': '${PROJECT_ROOT}'}]})
        self.assertEqual('cd ${PROJECT_ROOT}; cat ${PROJECT_ROOT}/src/a.py',
                         redactor.text('cd /home/fake/project; cat /home/fake/project/src/a.py'))
        paths = redactor.clean(['/home/fake/a', '/home/fake/b', '/home/fake/a'])
        self.assertNotEqual(paths[0], paths[1])
        self.assertEqual(paths[0], paths[2])
        self.assertNotIn('fake', json.dumps(dict(redactor.counts)))

    def test_path_redaction_preserves_adjacent_chinese_explanation(self):
        text = '在源码目录（/home/synthetic-user/project），导入失败；退出码为 1。'
        self.assertEqual('在源码目录（${PRIVATE_PATH_1}），导入失败；退出码为 1。', Redactor().text(text))
        redactor = Redactor({'path_aliases': [{'prefix': '~/private-project', 'replacement': '${PROJECT_ROOT}'}]})
        self.assertEqual('cd ${PROJECT_ROOT}; bash ${PROJECT_ROOT}/scripts/run.sh',
                         redactor.text('cd ~/private-project; bash ~/private-project/scripts/run.sh'))
        self.assertEqual('<hash>/data/data/narrativeqa.jsonl', Redactor().text('<hash>/data/data/narrativeqa.jsonl'))

    def test_public_sources_numeric_evidence_and_system_paths_are_preserved(self):
        data = {'source': 'https://github.com/example/repo/blob/' + 'a'*40 + '/home/test.py',
                'command': '/usr/bin/python /opt/tool/test.py /dev/null',
                'version': '10.2.1.3', 'token': 'hello', 'logprob': -1.3,
                'shape': [8, 128, 256], 'token_count': 4096, 'batch': 8, 'dtype': 'bf16'}
        self.assertEqual(data, Redactor().clean(data))
        self.assertEqual('token=128', Redactor().text('token=128'))
        self.assertEqual('sk = record.get("simplifiedKey", [])', Redactor().text('sk = record.get("simplifiedKey", [])'))
        self.assertEqual({'sk': 128, 'ak': 16}, Redactor().clean({'sk': 128, 'ak': 16}))
        self.assertEqual('git@github.com:example/repo.git', Redactor().text('git@github.com:example/repo.git'))
        self.assertEqual({'token': 'the', 'logprobs': [-1.2]}, Redactor().clean({'token': 'the', 'logprobs': [-1.2]}))

    def test_publication_findings_are_safe_and_fail_closed(self):
        text = '# Synthetic\n```sh\ncd /home/synthetic-user/project\n```\n见候选 c1\n'
        findings = publication_findings(text)
        self.assertIn({'line': 3, 'category': 'privacy_path'}, findings)
        self.assertIn({'line': 5, 'category': 'unresolved_internal_reference'}, findings)
        self.assertNotIn('synthetic-user', json.dumps(findings))
        with self.assertRaisesRegex(ValueError, 'publication audit failed'):
            require_publication_clean(text)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'card.md').write_text(text)
            report = audit(root, ['card.md'])
            self.assertFalse(report['ok'])
            self.assertFalse(report['semantic_review_pass'])
            self.assertNotIn('synthetic-user', json.dumps(report))
            (root / 'link.md').symlink_to(root / 'card.md')
            with self.assertRaises(ValueError):
                audit(root, ['link.md'])
            with self.assertRaises(ValueError):
                audit(root, ['../card.md'])

    def test_malformed_policy_is_rejected_without_echoing_values(self):
        for policy in [{'path_aliases': 'private'}, {'path_aliases': ['private']}, {'private_terms': 'private'}]:
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                Redactor(policy)

    def test_header_credentials_and_prefixed_secret_fields(self):
        raw = {'DB_PASSWORD': 'synthetic-password', 'OBS_AK': 'synthetic-key',
               'headers': 'Authorization: Basic c3ludGhldGlj\nCookie: a=secret1; b=secret2\n',
               'command': 'AK=ABCDEFGHIJKLMNOPQRST'}
        result = Redactor().clean(raw)
        for value in ['synthetic-password', 'synthetic-key', 'c3ludGhldGlj', 'secret1', 'secret2', 'ABCDEFGHIJKLMNOPQRST']:
            self.assertNotIn(value, json.dumps(result))
        self.assertEqual(result, Redactor().clean(result))

    def test_private_url_hosts_are_case_insensitive_and_idempotent(self):
        redactor = Redactor()
        original = 'https://FakeUser:synthetic-password@INTRA.CORP:8443/data/file?token=synthetic-token'
        cleaned = redactor.text(original)
        for value in ['FakeUser', 'synthetic-password', 'INTRA.CORP', 'synthetic-token']:
            self.assertNotIn(value, cleaned)
        self.assertEqual(cleaned, redactor.text(cleaned))
        self.assertEqual([], publication_findings(cleaned))
        other = redactor.text('https://FakeUser:password@PRIVATE:8443/api')
        self.assertNotIn('@private:', other.lower())
        self.assertIn('${PRIVATE_HOST_', other.rsplit('@', 1)[-1])
        self.assertEqual(other, redactor.text(other))
        public = 'https://[2001:db8::1]:8443/api'
        self.assertEqual(public, redactor.text(public))

    def test_private_endpoints_at_markdown_and_chinese_boundaries(self):
        for value in ['[诊断](https://INTRA.CORP)', '连接node.internal时失败',
                      '地址192.168.1.4。', 'address=192.168.1.4.', 'https://node.internal.']:
            with self.subTest(value=value):
                redactor = Redactor()
                self.assertTrue(publication_findings(value))
                cleaned = redactor.text(value)
                for private in ['INTRA.CORP', 'node.internal', '192.168.1.4']:
                    self.assertNotIn(private, cleaned)
                self.assertEqual(cleaned, redactor.text(cleaned))
                self.assertEqual([], publication_findings(cleaned))

    def test_python_local_constructor_is_not_treated_as_a_hostname(self):
        text = 'state = threading.local()'
        self.assertEqual(text, Redactor().text(text))
