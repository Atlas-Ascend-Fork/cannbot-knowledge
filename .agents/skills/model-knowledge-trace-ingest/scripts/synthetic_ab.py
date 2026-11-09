"""Reproduce offline single-source versus batch transport with public synthetic data."""

import argparse
import hashlib
import json
from pathlib import Path

from batch_exchange import reading_view
from evidence_bundle import build as evidence_bundle
from model_trace_common import canonical
from normalize_trace import normalize
from read_trace import read_event
import trace_batch


def run(output):
    output = trace_batch.fresh_output(output)
    output.mkdir(parents=True)
    report = {'schema_version': 'model.trace-synthetic-ab.v1', 'dataset': 'synthetic-model-trace-v1',
              'model_calls': 0, 'network_calls': 0, 'semantic_mining_performed': False,
              'timing_or_token_savings_measured': False, 'cases': []}
    for label, size in [('short', 128), ('long', 120000)]:
        root = output / label
        root.mkdir()
        sources, samples, raw_hashes = [], {}, []
        for number in range(4):
            raw = root / ('source_' + str(number) + '.jsonl')
            payload = 'SYNTHETIC observation\r\n' + 'x' * size + '\nSYNTHETIC_END'
            rows = [{'role': 'system', 'content': 'SYNTHETIC historical template'},
                    {'role': 'user', 'content': 'SYNTHETIC framework task ' + str(number)},
                    {'role': 'tool', 'content': payload}]
            raw.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            raw_hashes.append(hashlib.sha256(raw.read_bytes()).hexdigest())
            directory = root / ('normalized_' + str(number))
            trace_batch.require(normalize(raw, directory)['ok'], 'fixture normalization failed')
            events = [json.loads(line) for line in (directory / 'normalized_trace.jsonl').read_text().splitlines()]
            trace_batch.require(events[2]['content']['text'] == payload, 'full model path lost input text')
            sources.append({'trace_id': 'synthetic_' + str(number), 'normalized_dir': str(directory)})
            samples[number] = {'raw_characters': len(payload), 'model_normalized_characters': len(payload)}
        selection = root / 'selected.json'
        trace_batch.write_json(selection, {'schema_version': trace_batch.LOCAL, 'traces': sources})
        trace_batch.prepare(selection, root / 'batch')
        reading_view(root / 'batch', root / 'view')
        view = json.loads((root / 'view/view.json').read_text())
        body = (root / 'view/reading.txt').read_bytes().decode('utf-8')
        pages, serialized_bytes, expected_characters = 0, 0, 0
        for source, info in zip(sources, view['sources']):
            trace_batch.require(info['included_sequences'] == [2, 3] and info['context_only_sequences'] == [1],
                                'unexpected synthetic evidence selection')
            for sequence in [2, 3]:
                offset, parts = 0, []
                while True:
                    page = read_event(source['normalized_dir'], sequence, offset, 6000)
                    pages += 1
                    serialized_bytes += len(json.dumps(page, ensure_ascii=False, indent=2).encode())
                    parts.extend(page['text_parts'])
                    offset = page['next_offset']
                    if not page['has_more']:
                        break
                text = ''.join(parts)
                expected_characters += len(text)
                trace_batch.require(text in body, 'batch view lost development text')
        trace_batch.require(expected_characters == view['selected_characters'], 'A/B selected text differs')
        trace_batch.prepare(selection, root / 'references', references_only=True)
        evidence_selection = root / 'evidence-selection.json'
        trace_batch.write_json(evidence_selection, [{'trace_id': source['trace_id'], 'sequences': [2, 3]}
                                                    for source in sources])
        evidence_bundle(root / 'references', evidence_selection, root / 'evidence', max_bytes=24000, context=0)
        bundle = json.loads((root / 'evidence/evidence.json').read_text())
        actual = {}
        for page in bundle['pages']:
            raw_page = (root / 'evidence' / page['path']).read_bytes()
            trace_batch.require(len(raw_page) <= 24000, 'bounded page exceeded client budget')
            for record in json.loads(raw_page)['records']:
                key = (record['trace_id'], record['sequence'])
                previous = actual.get(key, '')
                trace_batch.require(len(previous) == record['offset'], 'evidence fragments not contiguous')
                actual[key] = previous + ''.join(record['text_parts'])
        for source in sources:
            events = map(json.loads, (Path(source['normalized_dir']) / 'normalized_trace.jsonl').read_text().splitlines())
            for event in events:
                if event['sequence'] in {2, 3}:
                    trace_batch.require(actual[(source['trace_id'], event['sequence'])] == event['content']['text'],
                                        'C evidence text differs from A/B')
        def storage_bytes(path):
            return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
        report['cases'].append({'name': label, 'sources': 4, 'selected_events': 8,
            'fixture_sha256': hashlib.sha256(canonical(raw_hashes)).hexdigest(),
            'A_single_source_pages': pages, 'A_serialized_page_bytes': serialized_bytes,
            'B_batch_reading_files': 1, 'B_reading_bytes': view['reading_bytes'],
            'B_materialized_preparation_bytes': storage_bytes(root / 'batch'),
            'C_reference_preparation_bytes': storage_bytes(root / 'references'),
            'C_evidence_pages': len(bundle['pages']), 'C_max_page_bytes': 24000,
            'C_evidence_page_bytes': sum(p['bytes'] for p in bundle['pages']),
            'C_exact_selected_text_preserved': True,
            'selected_characters_equal': True, 'exact_development_text_preserved': True,
            'normalization_comparison': samples})
    trace_batch.write_json(output / 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.output), ensure_ascii=False, indent=2))
