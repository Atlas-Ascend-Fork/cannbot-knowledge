"""Prepare bounded multi-source evidence pages without interpreting or executing them."""

import copy
import hashlib
import json
from pathlib import Path

from model_trace_common import canonical, sha256_file
import trace_batch


def encoded(records):
    return (json.dumps({'schema_version': 'model.trace-evidence-page.v1',
                        'historical_commands_are_data_only': True, 'records': records},
                       ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def build(batch, selection_path, output, max_bytes=24000, context=1):
    if not 4096 <= max_bytes <= 524288 or type(context) is not int or not 0 <= context <= 10:
        raise ValueError('invalid evidence byte budget or context radius')
    root, manifest = trace_batch.load_batch(batch)
    selections = json.loads(Path(selection_path).read_text())
    if not isinstance(selections, list) or not selections:
        raise ValueError('evidence selection must be a nonempty array')
    by_id = {s['trace_id']: s for s in manifest['sources']}
    ids = [s.get('trace_id') for s in selections]
    if len(set(ids)) != len(ids) or not set(ids) <= by_id.keys():
        raise ValueError('duplicate or foreign evidence source')
    destination = trace_batch.fresh_output(output)
    records, pages, sources, selected_characters = [], [], [], 0

    def flush():
        nonlocal records
        if records:
            pages.append(encoded(records))
            records = []

    for selection in selections:
        source = by_id[selection['trace_id']]
        directory = Path(source['source']['normalized_dir'])
        if destination.is_relative_to(directory.resolve()):
            raise ValueError('evidence output cannot be inside normalized sources')
        trace = directory / 'normalized_trace.jsonl'
        if (sha256_file(trace) != source['source']['normalized_trace_sha256'] or
                sha256_file(directory / 'session_manifest.json') != source['session_manifest_sha256']):
            raise ValueError('source changed before evidence preparation')
        requested = selection.get('sequences')
        if not isinstance(requested, list) or not requested or any(
                type(n) is not int or not 1 <= n <= source['events'] for n in requested):
            raise ValueError('evidence sequences must identify existing events')
        wanted = set(requested)
        # First pass finds explicit call/result pairs and neighbours without keeping a whole trace in RAM.
        pairs, meta = {}, {}
        with trace.open() as handle:
            for line in handle:
                event = json.loads(line)
                number = event['sequence']
                tool = event.get('tool') or {}
                call = tool.get('call_id')
                meta[number] = event['event_type']
                if call is not None and event['event_type'] in {'tool_call', 'tool_result', 'error'}:
                    key = canonical([event.get('session_id'), call])
                    pairs.setdefault(key, []).append(number)
        if context:
            wanted |= {n for seq in requested for n in range(max(1, seq-context), min(source['events'], seq+context)+1)
                       if meta[n] not in {'reasoning', 'system_message'}}
        for numbers in pairs.values():
            if wanted.intersection(numbers):
                wanted.update(numbers)
        with trace.open() as handle:
            for line in handle:
                event = json.loads(line)
                if event['sequence'] not in wanted:
                    continue
                text = event['content']['text']
                selected_characters += len(text)
                metadata = copy.deepcopy(event)
                metadata['content'].pop('text')
                offset = 0
                while True:
                    available = min(12000, len(text) - offset)

                    def page(size):
                        end = offset + size
                        fragment = text[offset:end]
                        return {'trace_id': source['trace_id'], **metadata, 'offset': offset,
                                'next_offset': end, 'total_characters': len(text),
                                'complete_event': offset == 0 and end == len(text),
                                'text_parts': [fragment[i:i+240] for i in range(0, len(fragment), 240)] or ['']}

                    minimum = 1 if available else 0
                    if len(encoded([*records, page(minimum)])) > max_bytes:
                        if not records:
                            raise ValueError('event metadata exceeds evidence budget')
                        flush()
                        continue
                    low, high = minimum, available
                    while low < high:
                        middle = (low + high + 1) // 2
                        if len(encoded([*records, page(middle)])) <= max_bytes:
                            low = middle
                        else:
                            high = middle - 1
                    records.append(page(low))
                    offset += low
                    if offset == len(text):
                        break
                    flush()
        if (sha256_file(trace) != source['source']['normalized_trace_sha256'] or
                sha256_file(directory / 'session_manifest.json') != source['session_manifest_sha256']):
            raise ValueError('source changed during evidence preparation')
        sources.append({**source, 'requested_sequences': sorted(set(requested)),
                        'included_sequences': sorted(wanted),
                        'unread_ranges': _unread(source['events'], wanted)})
    flush()
    destination.mkdir(parents=True)
    inventory = []
    for index, raw in enumerate(pages, 1):
        name = f'page_{index:05d}.json'
        (destination / name).write_bytes(raw)
        inventory.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    result = {'schema_version': 'model.trace-evidence-bundle.v1',
              'batch_manifest': str(root / 'manifest.json'),
              'batch_manifest_sha256': sha256_file(root / 'manifest.json'),
              'selection_sha256': sha256_file(selection_path), 'sources': sources, 'pages': inventory,
              'max_page_bytes': max_bytes, 'selected_characters': selected_characters,
              'preparation_is_not_semantic_reading': True, 'knowledge_written': False}
    trace_batch.write_json(destination / 'evidence.json', result)
    return {'ok': True, 'sources': len(sources), 'pages': len(inventory), 'max_page_bytes': max_bytes,
            'selected_characters': selected_characters, 'manifest': str(destination / 'evidence.json')}


def _unread(count, selected):
    spans = []
    for n in range(1, count + 1):
        if n in selected:
            continue
        if spans and spans[-1][1] + 1 == n:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    return spans
