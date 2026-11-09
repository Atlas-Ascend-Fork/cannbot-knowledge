"""Offline reading views and lossless transport of model-authored batch files."""

import argparse
import json
from pathlib import Path

from model_trace_common import child, sha256_file
from mining_sources import candidate_sources
import trace_batch


def ranges(sequences):
    spans = []
    for sequence in sequences:
        if spans and spans[-1][1] + 1 == sequence:
            spans[-1][1] = sequence
        else:
            spans.append([sequence, sequence])
    return spans


def reading_view(batch, output, max_bytes=524288):
    root, manifest = trace_batch.load_batch(batch)
    output = trace_batch.fresh_output(output)
    blocks, sources, selected_characters = [], [], 0
    for source in manifest['sources']:
        descriptor = source['source']
        directory = Path(descriptor['normalized_dir'])
        trace = directory / 'normalized_trace.jsonl'
        trace_batch.require(sha256_file(trace) == descriptor['normalized_trace_sha256']
                            and sha256_file(directory / 'session_manifest.json') == source['session_manifest_sha256'],
                            'source changed before rendering')
        blocks.append('\nTRACE ' + source['trace_id'] + '\n')
        included, excluded, index = [], [], []
        with trace.open() as handle:
            for line in handle:
                event = json.loads(line)
                sequence, text = event['sequence'], event['content']['text']
                omitted = event['event_type'] == 'reasoning' or (
                    event['event_type'] == 'system_message')
                index.append({'sequence': sequence, 'metadata': {**event, 'content': {
                    key: value for key, value in event['content'].items() if key != 'text'}},
                              'characters': len(text), 'included': not omitted})
                if omitted:
                    excluded.append(sequence)
                    continue
                included.append(sequence)
                header = {key: event.get(key) for key in ['sequence', 'actor', 'event_type', 'tool', 'timestamp']}
                header.update({key: event[key] for key in ('outcome', 'result_metadata', 'limitations',
                                                          'session_id', 'parent_session_id',
                                                          'message_id', 'parent_message_id') if key in event})
                blocks.extend(['\nEVENT ' + json.dumps(header, ensure_ascii=False) + '\n',
                               'TEXT_CHARACTERS ' + str(len(text)) + '\n', text, '\nEND_EVENT\n'])
                selected_characters += len(text)
        trace_batch.require(sha256_file(trace) == descriptor['normalized_trace_sha256'], 'source changed during rendering')
        sources.append({**source, 'included_sequences': included, 'context_only_sequences': excluded,
                        'included_ranges': ranges(included),
                        'event_index': index})
    body = ''.join(blocks)
    trace_batch.require(len(body.encode()) <= max_bytes, 'reading view exceeds budget; choose a smaller batch or a bounded window')
    output.mkdir(parents=True)
    (output / 'reading.txt').write_text(body)
    result = {'schema_version': 'model.trace-reading-view.v1', 'batch_manifest': str(root / 'manifest.json'),
              'batch_manifest_sha256': sha256_file(root / 'manifest.json'), 'sources': sources,
              'reading_sha256': sha256_file(output / 'reading.txt'), 'reading_bytes': len(body.encode()),
              'selected_characters': selected_characters, 'original_characters': manifest['stats']['characters'],
              'scope': 'development events; historical system templates and reasoning are indexed context only',
              'preparation_is_not_semantic_reading': True}
    trace_batch.write_json(output / 'view.json', result)
    return {key: result[key] for key in ['reading_bytes', 'selected_characters', 'original_characters', 'reading_sha256']}


def load_view(view):
    root = Path(view).resolve()
    if (root / 'view.json').exists():
        info = json.loads((root / 'view.json').read_text())
        trace_batch.require(info.get('schema_version') == 'model.trace-reading-view.v1', 'unsupported reading view')
        trace_batch.require(sha256_file(root / 'reading.txt') == info['reading_sha256'], 'reading view changed')
    else:
        evidence_path = root / 'evidence.json'
        info = json.loads(evidence_path.read_text())
        trace_batch.require(info.get('schema_version') == 'model.trace-evidence-bundle.v1', 'unsupported evidence bundle')
        for page in info['pages']:
            path = child(root, page['path'])
            trace_batch.require(path.stat().st_size == page['bytes'] and sha256_file(path) == page['sha256'],
                                'evidence page changed')
        info['reading_sha256'] = sha256_file(evidence_path)
    trace_batch.require(sha256_file(info['batch_manifest']) == info['batch_manifest_sha256'], 'batch changed')
    return root, info


def unpack(view, response, output):
    _, info = load_view(view)
    raw = Path(response).read_bytes().decode('utf-8').strip()
    if raw.startswith('```json\n') and raw.endswith('\n```'):
        raw = raw[8:-4]
    bundle = json.loads(raw)
    trace_batch.require(bundle.get('schema_version') == 'model.trace-file-bundle.v1', 'unsupported file bundle')
    trace_batch.require(bundle.get('batch_manifest_sha256') == info['batch_manifest_sha256'], 'bundle batch binding differs')
    files = bundle.get('files')
    trace_batch.require(isinstance(files, dict) and {'manifest.json', 'batch-report.json'} <= files.keys(),
                        'bundle must include the batch manifest and report')
    report = files['batch-report.json'].get('json', {})
    trace_batch.require(isinstance(report.get('traces'), list), 'report requires traces')
    trace_batch.require(all(isinstance(row, dict) and {'trace_id', 'disposition', 'candidate_ids', 'reason'} <= row.keys()
                            for row in report['traces']), 'report entry lacks required fields')
    output = trace_batch.fresh_output(output)
    prepared = []
    for name, item in files.items():
        path = child(output, name)
        trace_batch.require(isinstance(item, dict) and len(item) == 1, 'file needs exactly json or text')
        if path.suffix == '.json':
            trace_batch.require('json' in item and isinstance(item['json'], dict), 'JSON artifact must be an object')
            content = json.dumps(item['json'], ensure_ascii=False, indent=2) + '\n'
        else:
            trace_batch.require(path.suffix == '.md' and path.name.startswith('DRAFT-')
                                and isinstance(item.get('text'), str), 'only JSON artifacts and DRAFT markdown allowed')
            content = item['text']
        prepared.append((path, content))
    by_source = {s['source']['normalized_dir']: s for s in info['sources']}
    mined = files['manifest.json']['json']

    def anchor_nodes(value):
        if isinstance(value, dict):
            if {'source', 'sequence'} <= value.keys():
                yield value
            for child_value in value.values():
                yield from anchor_nodes(child_value)
        elif isinstance(value, list):
            for child_value in value:
                yield from anchor_nodes(child_value)

    for candidate in mined.get('candidates', []):
        reconstruction_path = str(candidate.get('route')) + '/reconstruction.json'
        trace_batch.require(reconstruction_path in files, 'candidate route requires reconstruction')
        traces = files[reconstruction_path]['json'].get('traces', [])
        descriptors = candidate_sources(mined, candidate)
        for descriptor in descriptors:
            trace_batch.require(sum(trace.get('source') == descriptor for trace in traces) == 1,
                                'candidate source requires one route reconstruction')
        for key in ['claims', 'evidence_roles', 'mechanism_artifacts']:
            for anchor in anchor_nodes(candidate.get(key)):
                trace_batch.require(type(anchor['source']) is int and 0 <= anchor['source'] < len(descriptors),
                                    'anchor index is outside candidate-local sources')
                trace_batch.require(type(anchor['sequence']) is int and anchor['sequence'] >= 1, 'invalid anchor sequence')
                source = by_source.get(descriptors[anchor['source']]['normalized_dir'])
                trace_batch.require(source and anchor['sequence'] in source['included_sequences'],
                                    'candidate anchor references context-only or unavailable events')
    for name, item in files.items():
        if not name.endswith('reconstruction.json'):
            continue
        reconstruction = item['json']
        trace_batch.require(reconstruction.get('schema_version') == 'model.trace-reconstruction.v1', 'invalid reconstruction')
        for trace in reconstruction.get('traces', []):
            source = by_source.get(trace.get('source', {}).get('normalized_dir'))
            trace_batch.require(source and trace['source'] == source['source'], 'foreign reconstruction source')
            allowed = set(source['included_sequences'])
            reviewed = set()
            for span in trace.get('coverage', {}).get('semantic_review_ranges', []):
                trace_batch.require(isinstance(span, list) and len(span) == 2 and all(type(x) is int for x in span)
                                    and 1 <= span[0] <= span[1] <= source['events'], 'invalid semantic coverage')
                reviewed.update(range(span[0], span[1] + 1))
            trace_batch.require(reviewed <= allowed, 'omitted context cannot be claimed as reviewed')
            for entry in trace.get('timeline', []) + trace.get('facts', []):
                trace_batch.require(set(entry.get('event_refs', [])) <= reviewed, 'fact references unread events')
    output.mkdir(parents=True)
    for path, content in prepared:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    result = trace_batch.check(Path(info['batch_manifest']).parent, output / 'batch-report.json', output / 'manifest.json')
    trace_batch.write_json(output / 'transport-receipt.json', {
        'schema_version': 'model.trace-file-transport.v1', 'response_sha256': sha256_file(response),
        'batch_manifest_sha256': info['batch_manifest_sha256'], 'reading_sha256': info['reading_sha256'],
        'files': {str(path.relative_to(output)): sha256_file(path) for path, _ in prepared},
        'model_authored_content_unchanged': True, 'knowledge_text_unchanged': True, 'semantic_or_independent_review_pass': False})
    return {**result, 'files': len(prepared), 'output': str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    view = commands.add_parser('view')
    view.add_argument('batch', type=Path)
    view.add_argument('--output', type=Path, required=True)
    view.add_argument('--max-bytes', type=int, default=524288)
    evidence = commands.add_parser('evidence')
    evidence.add_argument('batch', type=Path)
    evidence.add_argument('--selection', type=Path, required=True)
    evidence.add_argument('--output', type=Path, required=True)
    evidence.add_argument('--max-bytes', type=int, default=24000)
    evidence.add_argument('--context', type=int, default=1)
    unpacker = commands.add_parser('unpack')
    unpacker.add_argument('view', type=Path)
    unpacker.add_argument('response', type=Path)
    unpacker.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'evidence':
            from evidence_bundle import build
            result = build(args.batch, args.selection, args.output, args.max_bytes, args.context)
        elif args.command == 'view':
            result = reading_view(args.batch, args.output, args.max_bytes)
        else:
            result = unpack(args.view, args.response, args.output)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
