#!/usr/bin/env python3
"""Normalize local Agent exports to a common, lossless-after-redaction event format."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from model_trace_common import REPOSITORY, canonical, redact_event, sha256_file
from trace_privacy import PROFILE as REDACTION_PROFILE, Redactor
from trace_adapters import Adapter, KINDS

MANIFEST = 'agent.trace-session.v1'
SUFFIXES = {'.json', '.jsonl', '.ndjson', '.txt', '.md', '.log'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def visible_unicode(value):
    if isinstance(value, str):
        return value.encode('utf-8', 'backslashreplace').decode('utf-8')
    if isinstance(value, list):
        return [visible_unicode(item) for item in value]
    if isinstance(value, dict):
        return {visible_unicode(k): visible_unicode(v) for k, v in value.items()}
    return value


def records(data, fmt, warnings):
    raw = data.decode('utf-8')
    if fmt == 'text':
        return [raw]
    try:
        value = json.loads(raw)
    except ValueError:
        if fmt == 'json':
            warnings.append('Invalid or incomplete JSON preserved as unknown; no missing suffix invented.')
            return [raw]
    else:
        return value if isinstance(value, list) else [value]
    result = []
    for line in raw.splitlines(keepends=True):
        if not line.strip():
            continue
        try:
            result.append(json.loads(line))
        except ValueError:
            result.append(line)
            warnings.append('Unparsed record preserved as unknown; raw source is needed for interpretation.')
    return result


def normalize(source, output, fmt='auto', mapping=None, layout='events', redaction_policy=None):
    require(fmt in {'auto', 'json', 'jsonl', 'text'}, 'unsupported input format')
    source = Path(source).expanduser().absolute()
    output = Path(output).expanduser().absolute()
    require(not any(p.is_symlink() for p in (source, *source.parents)), 'symlink source path')
    require(not output.exists() and not any(p.is_symlink() for p in (output, *output.parents)),
            'normalization requires a fresh output without symlink ancestors')
    source, output = source.resolve(), output.resolve()
    require(not output.is_relative_to(REPOSITORY / 'knowledge'), 'output cannot be knowledge')
    require(not source.is_dir() or not output.is_relative_to(source), 'output cannot be inside raw source')
    if isinstance(mapping, dict):
        layout = mapping.get('layout', layout)
    require(layout in {'events', 'snapshots'}, 'unknown input layout')
    if layout == 'snapshots':
        require(mapping is None or isinstance(mapping, dict), 'snapshot mapping must be an object')
        for key in ('messages_path', 'response_path', 'session_id', 'parent_session_id'):
            require(not mapping or key not in mapping or isinstance(mapping[key], str) and bool(mapping[key]),
                    'snapshot paths must be nonempty strings')
    elif mapping is not None:
        require(isinstance(mapping, dict) and isinstance(mapping.get('fields'), dict), 'mapping requires fields')
        require({'event_type', 'text'} <= mapping['fields'].keys(), 'mapping requires event_type and text paths')
        require(all(isinstance(p, str) and p for p in mapping['fields'].values()), 'mapping paths must be strings')
    paths = sorted(source.rglob('*')) if source.is_dir() else [source]
    files = []
    for path in paths:
        require(not path.is_symlink(), 'symlink source member')
        if path.is_dir():
            continue
        require(path.is_file() and path.suffix.lower() in SUFFIXES, 'unsupported source member: ' + path.name)
        files.append(path)
    require(files, 'empty source')
    identities, events, warnings, redactions = [], [], [], 0
    redactor = Redactor(redaction_policy)
    histories = {}
    for path in files:
        name = str(path.relative_to(source)) if source.is_dir() else path.name
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        identities.append({'path': name, 'sha256': file_hash})
        adapter = Adapter('file:' + name, mapping if layout == 'events' else None)
        adapter.snapshot_histories = histories
        selected = 'text' if fmt == 'auto' and path.suffix.lower() in {'.txt', '.md'} else fmt
        for index, record in enumerate(records(data, selected, warnings), 1):
            converted = adapter.snapshot(record, mapping) if layout == 'snapshots' else adapter.convert(record)
            for item in converted:
                locator = item.pop('locator')
                item['sequence'] = len(events) + 1
                item['provenance'] = {'raw_source': name, 'raw_record': index, 'raw_sha256': digest(record),
                                      'raw_file_sha256': file_hash, 'locator': locator,
                                      'adapter': 'snapshot-prefix-v1' if layout == 'snapshots' else 'structural-v1',
                                      'content_identity_sha256': digest(item['content'])}
                clean, count = redact_event(item, redactor)
                clean['provenance']['content_identity_sha256'] = digest(clean['content'])
                clean['provenance']['redaction_profile'] = REDACTION_PROFILE
                redactions += count
                warnings.extend(clean.get('limitations', []))
                safe = visible_unicode(clean)
                safe['provenance']['content_identity_sha256'] = digest(safe['content'])
                if clean != safe:
                    warnings.append('Invalid Unicode units retained as visible escapes; raw hash keeps their identity.')
                events.append(safe)
            warnings.extend(adapter.warnings)
            adapter.warnings.clear()
        require(sha256_file(path) == file_hash, 'raw source changed during normalization')
    kinds = Counter(e['event_type'] for e in events)
    trace = ''.join(json.dumps(e, ensure_ascii=False, sort_keys=True) + '\n' for e in events).encode()
    manifest = {'schema_version': MANIFEST, 'source': {'sha256': digest(identities), 'files': identities},
                'normalized_trace_sha256': hashlib.sha256(trace).hexdigest(),
                'sessions': sorted({str(e['session_id']) for e in events}),
                'coverage': {'normalized_events': len(events), 'unknown_events': kinds['unknown'],
                             'event_types': dict(kinds), 'redactions': redactions},
                'warnings': sorted(set(warnings)), 'mapping': mapping, 'layout': layout,
                'redaction': {'profile': REDACTION_PROFILE, 'categories': dict(redactor.counts),
                              'caller_policy_used': redaction_policy is not None},
                'source_capture_limitations': sorted(set(warnings)),
                'normalization_is_not_semantic_review': True}
    output.mkdir(parents=True)
    (output / 'normalized_trace.jsonl').write_bytes(trace)
    (output / 'session_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return verify(output)


def verify(directory):
    root = Path(directory)
    manifest = json.loads((root / 'session_manifest.json').read_text())
    require(manifest.get('schema_version') == MANIFEST, 'normalize this input to agent.trace-session.v1 first')
    require(digest(manifest['source']['files']) == manifest['source']['sha256'], 'source inventory hash mismatch')
    require(sha256_file(root / 'normalized_trace.jsonl') == manifest['normalized_trace_sha256'],
            'normalized content hash changed')
    counts = Counter()
    for index, line in enumerate((root / 'normalized_trace.jsonl').read_text().splitlines(), 1):
        event = json.loads(line)
        require(event.get('schema_version') == 'trace.event.v1' and event.get('sequence') == index,
                'invalid normalized event sequence or schema')
        require(event.get('event_type') in KINDS and isinstance(event.get('actor'), str), 'invalid event kind or actor')
        require(isinstance(event.get('content', {}).get('text'), str), 'event text must be a string')
        provenance = event.get('provenance', {})
        require(isinstance(provenance.get('raw_record'), int) and provenance['raw_record'] > 0
                and provenance.get('raw_source') and len(provenance.get('raw_sha256', '')) == 64,
                'missing raw record provenance')
        counts[event['event_type']] += 1
    coverage = manifest['coverage']
    require(sum(counts.values()) == coverage['normalized_events'] and dict(counts) == coverage['event_types']
            and counts['unknown'] == coverage['unknown_events'], 'event coverage differs from manifest')
    return {'ok': True, 'events': sum(counts.values()), 'unknown_events': counts['unknown']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--format', choices=['auto', 'json', 'jsonl', 'text'], default='auto')
    parser.add_argument('--mapping', type=Path)
    parser.add_argument('--redaction-policy', type=Path, help='private declarative path aliases and literal terms')
    parser.add_argument('--layout', choices=['events', 'snapshots'], default='events')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify and args.output is None:
        parser.error('--output is required unless --verify is given')
    try:
        result = verify(args.source) if args.verify else normalize(
            args.source, args.output, args.format, json.loads(args.mapping.read_text()) if args.mapping else None,
            args.layout, json.loads(args.redaction_policy.read_text()) if args.redaction_policy else None)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'ok': False, 'error': str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
