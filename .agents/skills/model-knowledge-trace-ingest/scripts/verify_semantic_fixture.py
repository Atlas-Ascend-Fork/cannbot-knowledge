#!/usr/bin/env python3
"""Replay public synthetic normalization and artifact integrity without a model call."""

import argparse
import hashlib
import json
from pathlib import Path

from model_trace_common import child, sha256_file
from trace_batch import fresh_output, normalize_batch


DATA = Path(__file__).resolve().parents[1] / 'references/semantic-evaluation'


def require(value, message):
    if not value:
        raise ValueError(message)


def verify(output):
    snapshots = json.loads((DATA / 'snapshot-reconstruction.json').read_text())
    for snapshot in snapshots:
        require(sha256_file(child(DATA, snapshot['patch'])) == snapshot['sha256'],
                'recorded snapshot patch bytes changed: ' + snapshot['arm'])
    fixture = json.loads((DATA / 'inputs.json').read_text())
    results = json.loads((DATA / 'results.json').read_text())
    require(fixture.get('synthetic_only') is True and results.get('synthetic_only') is True,
            'only explicitly synthetic fixtures are accepted')
    require(results.get('evaluation_complete') is True, 'semantic trial records are incomplete')
    require(sha256_file(DATA / 'inputs.json') == results['input_manifest_sha256'],
            'fixture manifest bytes changed')
    traces = fixture['traces']
    identities = {row['trace_id'] for row in traces}
    require(len(identities) == len(traces), 'duplicate fixture identity')
    for row in traces:
        require(sha256_file(child(DATA, row['file'])) == row['sha256'], 'fixture bytes changed')
    for arm in results['arms'].values():
        require({row['trace_id'] for row in arm['dispositions']} == identities,
                'published outcomes do not cover the input batch')
        for card in arm['cards']:
            content = child(DATA, card['file']).read_text()
            require(hashlib.sha256(content.encode()).hexdigest() == card['sha256'],
                    'published staged card bytes changed')
            require('合成' in content or 'SYNTHETIC' in content,
                    'synthetic card label is missing')
        for review in arm['reviews']:
            receipt_path = child(DATA, review['file'])
            require(sha256_file(receipt_path) == review['sha256'], 'recorded receipt bytes changed')
            receipt = json.loads(receipt_path.read_text())
            require(receipt['subject']['subject_sha256'] == review['subject_sha256'] and
                    receipt['verdict'] == review['verdict'], 'recorded review differs from summary')
    output = fresh_output(output)
    output.mkdir(parents=True)
    selected = {'schema_version': 'model.trace-local-batch.v1', 'traces': [
        {'trace_id': row['trace_id'], 'path': str(child(DATA, row['file'])),
         'source_family': row['source_family']} for row in traces]}
    selected_path = output / 'input.json'
    selected_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
    normalize_batch(selected_path, output / 'normalized')
    for row in results['arms']['proposed']['normalized_sources']:
        manifest = json.loads((output / 'normalized' / row['trace_id'] / 'session_manifest.json').read_text())
        require(manifest['source']['sha256'] == row['raw_source_sha256'] and
                manifest['normalized_trace_sha256'] == row['normalized_trace_sha256'],
                'current normalization differs from the evaluated proposed snapshot: ' + row['trace_id'])
    report = {'ok': True, 'traces': len(traces), 'model_calls': 0, 'knowledge_written': False,
              'semantic_review_pass': False,
              'checks': ['synthetic input bytes', 'actual outcome coverage', 'staged card bytes',
                         'recorded receipt bytes', 'current normalization replay'],
              'limitations': ['Artifact integrity does not authenticate a reviewer or repeat semantic mining.',
                              'Fresh semantic evaluation requires an external client and an independent reviewer.']}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.output), ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
