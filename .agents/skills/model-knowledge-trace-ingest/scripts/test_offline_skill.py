"""Offline workflow and boundaries for a Skill executed by its calling Agent."""

import ast
import json
from pathlib import Path
import tempfile
import unittest

from read_trace import batch, read_event


class OfflineNormalizationTests(unittest.TestCase):
    def test_batch_reader_preserves_all_events_under_utf8_output_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            texts = ['first', '', '汉字\x00' * 6000, 'last', '']
            source = [{'sequence': index, 'actor': 'tool', 'event_type': 'tool_result', 'content': {'text': text},
                       'provenance': {'raw_source': 'synthetic'}} for index, text in enumerate(texts, 1)]
            (root / 'normalized_trace.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in source))
            actual = {index: '' for index in range(1, len(texts) + 1)}
            sequence, offset, calls, multiple = 1, 0, 0, False
            while True:
                result = batch(root, sequence, offset)
                serialized = json.dumps(result, ensure_ascii=False, indent=2)
                self.assertLess(len(serialized.encode()), 24000)
                self.assertTrue(all(len(line) < 2000 for line in serialized.splitlines()))
                multiple |= len(result['pages']) > 1
                for page in result['pages']:
                    self.assertEqual(len(actual[page['sequence']]), page['offset'])
                    actual[page['sequence']] += ''.join(page['text_parts'])
                sequence, offset = result['next_sequence'], result['next_offset']
                calls += 1
                self.assertLess(calls, 100)
                if not result['has_more']:
                    break
            self.assertEqual(texts, list(actual.values()))
            self.assertTrue(multiple)
            for args in [(0, 0), (1, 100), (100, 0)]:
                with self.assertRaises(ValueError):
                    batch(root, *args)

    def test_long_event_reader_covers_exact_characters_in_short_output_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = '汉字\n' + '\x00' * 2000 + 'x' * 15000 + 'SYNTHETIC_END'
            event = {'sequence': 1, 'actor': 'tool', 'event_type': 'tool_result',
                     'content': {'text': original}, 'provenance': {'raw_source': 'synthetic'}}
            (root / 'normalized_trace.jsonl').write_text(json.dumps(event) + '\n')
            text = ''
            offset = 0
            while True:
                page = read_event(root, 1, offset, 6000)
                self.assertEqual(offset, page['offset'])
                self.assertTrue(all(len(line) < 2000 for line in json.dumps(page, ensure_ascii=False, indent=2).splitlines()))
                text += ''.join(page['text_parts'])
                offset = page['next_offset']
                if not page['has_more']:
                    break
            self.assertEqual(original, text)
            self.assertEqual(len(original), offset)
            with self.assertRaises(ValueError):
                read_event(root, 1, offset + 1)



class SkillArchitectureTests(unittest.TestCase):
    def test_production_helpers_have_no_model_client_or_scheduler(self):
        scripts = Path(__file__).parent
        forbidden_modules = {'subprocess', 'obs', 'httpx', 'requests', 'full_trace_runtime', 'logclassify'}
        forbidden_calls = {'system', 'popen', 'Popen', 'execv', 'execl', 'spawn', 'enqueue', 'job_prompt'}
        for path in scripts.glob('*.py'):
            if path.name.startswith('test_'):
                continue
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        self.assertFalse(forbidden_modules & {item.name.split('.')[0] for item in node.names})
                    elif isinstance(node, ast.ImportFrom):
                        self.assertNotIn((node.module or '').split('.')[0], forbidden_modules)
                    elif isinstance(node, ast.Call):
                        name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
                        self.assertNotIn(name, forbidden_calls)


if __name__ == '__main__':
    unittest.main()
