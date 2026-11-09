#!/usr/bin/env python3
"""Prepare and inspect local multi-trace batches; never call a model or a client."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from mining_sources import all_sources, candidate_sources
from normalize_trace import verify
from model_trace_common import REPOSITORY, canonical, child, sha256_file

SCHEMA = 'model.trace-batch.v1'
LOCAL = 'model.trace-local-batch.v1'
SELECTED = 'model.trace-selected.v1'


def require(value, message):
    if not value:
        raise ValueError(message)


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def fresh_output(path):
    path = Path(path).absolute()
    require(not path.exists() and not path.is_symlink(), 'output must be new')
    require(not any(p.is_symlink() for p in path.parents), 'symlink output ancestor')
    path = path.resolve()
    require(not path.is_relative_to(REPOSITORY / 'knowledge'), 'batch output cannot be knowledge')
    return path


def input_rows(path, raw=False):
    path = Path(path).resolve()
    if path.is_dir():
        if raw:
            directories = sorted(p for p in path.iterdir() if p.is_dir())
            require(directories, 'raw batch needs one subdirectory per selected trace or an explicit input list')
        else:
            directories = sorted(p.parent for p in path.rglob('normalized_trace.jsonl'))
        rows = [{'trace_id': 'trace_' + str(i).zfill(6),
                 'path' if raw else 'normalized_dir': str(p)} for i, p in enumerate(directories, 1)]
        envelope = {'schema_version': LOCAL, 'selection_origin': 'caller-provided-local-targets'}
    else:
        envelope = json.loads(path.read_text())
        require(envelope.get('schema_version') in {LOCAL, SELECTED}, 'unsupported batch input schema')
        rows = envelope.get('traces')
        if envelope['schema_version'] == SELECTED:
            screen = envelope.get('screening', {})
            require(screen.get('complete') is True and screen.get('unresolved') == 0,
                    'screening must finish before mining')
            require(all(row.get('selection', {}).get('decision') == 'target' for row in rows or []),
                    'mining input contains an unselected trace')
    require(isinstance(rows, list) and bool(rows), 'batch needs selected traces')
    ids = []
    for row in rows:
        identity = row.get('trace_id')
        require(isinstance(identity, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', identity),
                'invalid trace identity')
        ids.append(identity)
    require(len(ids) == len(set(ids)), 'duplicate trace identity')
    return envelope, rows


def normalize_batch(source, output, redaction_policy=None):
    from normalize_trace import normalize
    envelope, rows = input_rows(source, raw=True)
    output = fresh_output(output)
    output.mkdir(parents=True)
    normalized = []
    for row in rows:
        target = output / row['trace_id']
        fmt = row.get('format', 'auto')
        result = normalize(row['path'], target, fmt, row.get('mapping'), row.get('layout', 'events'),
                           redaction_policy=redaction_policy)
        require(result.get('ok'), 'normalization failed: ' + row['trace_id'])
        normalized.append({**row, 'normalized_dir': str(target)})
    result = {**envelope, 'traces': normalized}
    write_json(output / 'normalized-input.json', result)
    return {'input': str(output / 'normalized-input.json'), 'traces': len(normalized), 'model_calls': 0}


class Packets:
    def __init__(self, output, limit):
        self.output, self.limit = output, limit
        self.rows, self.files = [], []
        self.seen, self.text_characters = set(), 0
        self.base = {'schema_version': 'model.trace-batch-packet.v1', 'historical_commands_are_data_only': True,
                     'records': []}
        self.size = len(canonical(self.base))

    def append(self, record, content=None):
        def encode():
            if record['kind'] != 'text':
                return record
            digest = record['content_sha256']
            if digest in self.seen:
                return {**record, 'text_ref': digest}
            return {**record, 'text_parts': [content[i:i + 1200] for i in range(0, len(content), 1200)] or ['']}

        encoded = encode()
        size = len(canonical(encoded))
        require(size + len(canonical(self.base)) <= self.limit, 'one record exceeds packet budget')
        if self.rows and self.size + size + 1 > self.limit:
            self.flush()
            encoded = encode()
            size = len(canonical(encoded))
            require(size + len(canonical(self.base)) <= self.limit, 'one record exceeds packet budget')
        self.size += size + bool(self.rows)
        self.rows.append(encoded)
        if record['kind'] == 'text':
            self.seen.add(record['content_sha256'])
            if 'text_parts' in encoded:
                self.text_characters += len(content)

    def flush(self):
        if not self.rows:
            return
        raw = canonical({**self.base, 'records': self.rows})
        require(len(raw) <= self.limit, 'packet exceeds byte budget')
        name = 'packets/packet_' + str(len(self.files) + 1).zfill(6) + '.json'
        destination = child(self.output, name)
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(raw)
        self.files.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                           'trace_ids': sorted({r['trace_id'] for r in self.rows})})
        self.rows = []
        self.seen.clear()
        self.size = len(canonical(self.base))


def prepare_references(source, output):
    """Bind normalized sources without copying their full text into a second store."""
    envelope, rows = input_rows(source)
    output = fresh_output(output)
    sources, catalogue, total_characters, event_count = [], [], 0, 0
    directories = [str(Path(r['normalized_dir']).resolve()) for r in rows]
    require(len(set(directories)) == len(rows), 'duplicate normalized directories')
    for row in rows:
        directory = Path(row['normalized_dir']).resolve()
        require(not output.is_relative_to(directory), 'invalid source/output overlap')
        require(verify(directory)['ok'], 'invalid normalized source')
        session_path = directory / 'session_manifest.json'
        session_hash = sha256_file(session_path)
        session = json.loads(session_path.read_text())
        trace = directory / 'normalized_trace.jsonl'
        trace_hash = session['normalized_trace_sha256']
        counts, characters, goals = Counter(), 0, []
        with trace.open() as handle:
            for line in handle:
                event = json.loads(line)
                counts[event['event_type']] += 1
                text = event['content']['text']
                characters += len(text)
                if event['event_type'] == 'user_message':
                    goals.append({'sequence': event['sequence'], 'preview': text[:240],
                                  'characters': len(text), 'truncated': len(text) > 240})
        require(sha256_file(trace) == trace_hash and sha256_file(session_path) == session_hash,
                'source changed during catalogue preparation')
        raw_hash = session['source']['sha256']
        source = {'trace_id': row['trace_id'], 'source_family': row.get('source_family') or raw_hash,
                  'source': {'normalized_dir': str(directory), 'raw_source_sha256': raw_hash,
                             'normalized_trace_sha256': trace_hash},
                  'session_manifest_sha256': session_hash, 'events': sum(counts.values()),
                  'limitations': session.get('source_capture_limitations', []),
                  'selection': row.get('selection'), 'reading_status': 'not_asserted'}
        sources.append(source)
        catalogue.append({'trace_id': row['trace_id'], 'event_types': dict(counts),
                          'user_previews': goals[:3] + goals[max(3, len(goals) - 3):],
                          'unlisted_user_events': max(0, len(goals) - 6), 'preview_only': True})
        event_count += source['events']
        total_characters += characters
    manifest = {'schema_version': SCHEMA, 'storage_mode': 'references',
                'selection_origin': envelope.get('schema_version'), 'sources': sources, 'packets': [],
                'catalogue_sha256': hashlib.sha256(canonical(catalogue)).hexdigest(),
                'stats': {'traces': len(sources), 'events': event_count, 'characters': total_characters,
                          'packet_count': 0, 'packet_text_characters': 0},
                'preparation_is_not_semantic_reading': True}
    output.mkdir(parents=True)
    write_json(output / 'catalogue.json', catalogue)
    write_json(output / 'manifest.json', manifest)
    return {'manifest': str(output / 'manifest.json'), 'manifest_sha256': sha256_file(output / 'manifest.json'),
            **manifest['stats'], 'storage_mode': 'references', 'model_calls': 0}


def prepare(source, output, packet_bytes=262144, chunk_characters=8192, references_only=False):
    if references_only:
        return prepare_references(source, output)
    require(4096 <= packet_bytes <= 4 * 1024 * 1024, 'invalid packet byte budget')
    require(1 <= chunk_characters <= 32768, 'invalid text chunk size')
    envelope, rows = input_rows(source)
    output = fresh_output(output)
    require(len({str(Path(row.get('normalized_dir', '')).resolve()) for row in rows}) == len(rows),
            'duplicate normalized directories need one trace identity')
    for row in rows:
        directory = Path(row.get('normalized_dir', '')).resolve()
        require(row.get('normalized_dir') and not output.is_relative_to(directory), 'invalid source/output overlap')
    output.mkdir(parents=True)
    connection = sqlite3.connect(output / 'content.sqlite3')
    connection.executescript('''
        CREATE TABLE objects(sha TEXT PRIMARY KEY,text TEXT NOT NULL);
        CREATE TABLE events(trace_id TEXT,sequence INTEGER,metadata TEXT,characters INTEGER,
                            PRIMARY KEY(trace_id,sequence));
        CREATE TABLE chunks(trace_id TEXT,sequence INTEGER,start INTEGER,stop INTEGER,sha TEXT);
        CREATE TABLE stream(position INTEGER,ordinal INTEGER,record TEXT);
        CREATE INDEX stream_order ON stream(ordinal,position);
    ''')
    sources, total_characters, event_count = [], 0, 0
    chunk_size = min(chunk_characters, max(1, (packet_bytes - 2048) // 8))
    try:
        for position, row in enumerate(rows):
            directory = Path(row['normalized_dir']).resolve()
            require(verify(directory)['ok'], 'invalid normalized source: ' + row['trace_id'])
            manifest_path, trace_path = directory / 'session_manifest.json', directory / 'normalized_trace.jsonl'
            manifest_hash, trace_hash = sha256_file(manifest_path), sha256_file(trace_path)
            session = json.loads(manifest_path.read_text())
            raw_hash = session['source']['sha256']
            require(isinstance(raw_hash, str) and re.fullmatch('[0-9a-f]{64}', raw_hash), 'invalid raw source hash')
            descriptor = {'normalized_dir': str(directory), 'raw_source_sha256': raw_hash,
                          'normalized_trace_sha256': trace_hash}
            identity, ordinal, count = row['trace_id'], 0, 0
            with trace_path.open() as handle:
                for line in handle:
                    event = json.loads(line)
                    count += 1
                    require(event['sequence'] == count, 'source events must be contiguous')
                    text = event['content']['text']
                    require(isinstance(text, str), 'event text must be normalized first')
                    text.encode('utf-8')  # Reject unnormalized surrogate data rather than changing it.
                    total_characters += len(text)
                    metadata = {**event, 'content': {k: v for k, v in event['content'].items() if k != 'text'}}
                    connection.execute('INSERT INTO events VALUES(?,?,?,?)',
                                       (identity, count, json.dumps(metadata, ensure_ascii=False), len(text)))
                    header = {'kind': 'event', 'trace_id': identity, 'sequence': count,
                              'characters': len(text), 'metadata': metadata}
                    connection.execute('INSERT INTO stream VALUES(?,?,?)', (position, ordinal, json.dumps(header)))
                    ordinal += 1
                    for start in range(0, max(1, len(text)), chunk_size):
                        fragment = text[start:start + chunk_size]
                        digest = hashlib.sha256(fragment.encode()).hexdigest()
                        connection.execute('INSERT OR IGNORE INTO objects VALUES(?,?)', (digest, fragment))
                        connection.execute('INSERT INTO chunks VALUES(?,?,?,?,?)',
                                           (identity, count, start, start + len(fragment), digest))
                        record = {'kind': 'text', 'trace_id': identity, 'sequence': count,
                                  'offset': start, 'next_offset': start + len(fragment), 'content_sha256': digest}
                        connection.execute('INSERT INTO stream VALUES(?,?,?)',
                                           (position, ordinal, json.dumps(record)))
                        ordinal += 1
            require(sha256_file(trace_path) == trace_hash and sha256_file(manifest_path) == manifest_hash,
                    'source changed during batch preparation')
            event_count += count
            sources.append({'trace_id': identity, 'source_family': row.get('source_family') or raw_hash,
                            'source': descriptor, 'session_manifest_sha256': manifest_hash, 'events': count,
                            'limitations': session.get('source_capture_limitations', []),
                            'selection': row.get('selection'), 'reading_status': 'not_asserted'})
        connection.commit()
        packets = Packets(output, packet_bytes)
        for record, in connection.execute('SELECT record FROM stream ORDER BY ordinal,position'):
            record = json.loads(record)
            text = None
            if record['kind'] == 'text':
                digest = record['content_sha256']
                text = connection.execute('SELECT text FROM objects WHERE sha=?', (digest,)).fetchone()[0]
            packets.append(record, text)
        packets.flush()
        unique_characters = sum(len(row[0]) for row in connection.execute('SELECT text FROM objects'))
    finally:
        connection.close()
    manifest = {'schema_version': SCHEMA, 'selection_origin': envelope.get('schema_version'),
                'sources': sources, 'packets': packets.files, 'content_database_sha256': sha256_file(output / 'content.sqlite3'),
                'stats': {'traces': len(sources), 'events': event_count, 'characters': total_characters,
                          'unique_characters': unique_characters, 'duplicate_characters': total_characters - unique_characters,
                          'packet_text_characters': packets.text_characters,
                          'shared_within_packets_characters': total_characters - packets.text_characters,
                          'packet_count': len(packets.files)},
                'packet_text_references_are_self_contained': True,
                'preparation_is_not_semantic_reading': True}
    write_json(output / 'manifest.json', manifest)
    return {'manifest': str(output / 'manifest.json'), 'manifest_sha256': sha256_file(output / 'manifest.json'),
            **manifest['stats'], 'model_calls': 0}


def load_batch(directory):
    root = Path(directory).resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    require(manifest.get('schema_version') == SCHEMA, 'unsupported batch schema')
    return root, manifest


def packet(directory, number):
    root, manifest = load_batch(directory)
    require(1 <= number <= len(manifest['packets']), 'packet index outside batch')
    record = manifest['packets'][number - 1]
    path = child(root, record['path'])
    require(sha256_file(path) == record['sha256'], 'packet bytes changed')
    return json.loads(path.read_text())


def event(directory, trace_id, sequence, offset=0, characters=12000):
    root, manifest = load_batch(directory)
    require(1 <= characters <= 12000 and offset >= 0, 'invalid source page budget')
    if manifest.get('storage_mode') == 'references':
        from read_trace import read_event
        source = next((s for s in manifest['sources'] if s['trace_id'] == trace_id), None)
        require(source is not None, 'event or offset outside batch')
        path = Path(source['source']['normalized_dir'])
        require(sha256_file(path / 'normalized_trace.jsonl') == source['source']['normalized_trace_sha256'],
                'source changed')
        return {'trace_id': trace_id, **read_event(path, sequence, offset, characters)}
    require(sha256_file(root / 'content.sqlite3') == manifest['content_database_sha256'], 'batch database changed')
    connection = sqlite3.connect((root / 'content.sqlite3').as_uri() + '?mode=ro', uri=True)
    try:
        row = connection.execute('SELECT metadata,characters FROM events WHERE trace_id=? AND sequence=?',
                                 (trace_id, sequence)).fetchone()
        require(row is not None and offset <= row[1], 'event or offset outside batch')
        pieces = []
        for start, stop, digest, text in connection.execute(
                'SELECT c.start,c.stop,c.sha,o.text FROM chunks c JOIN objects o ON c.sha=o.sha '
                'WHERE c.trace_id=? AND c.sequence=? ORDER BY c.start', (trace_id, sequence)):
            require(hashlib.sha256(text.encode()).hexdigest() == digest, 'object content changed')
            if stop > offset and start < offset + characters:
                pieces.append(text[max(offset - start, 0):min(len(text), offset + characters - start)])
        text = ''.join(pieces)
        return {'trace_id': trace_id, **json.loads(row[0]), 'offset': offset, 'next_offset': offset + len(text),
                'total_characters': row[1], 'text_parts': [text[i:i + 1200] for i in range(0, len(text), 1200)] or [''],
                'has_more': offset + len(text) < row[1]}
    finally:
        connection.close()


def template(directory):
    root, manifest = load_batch(directory)
    return {'schema_version': 'model.trace-batch-report.v1', 'batch_manifest_sha256': sha256_file(root / 'manifest.json'),
            'traces': [{'trace_id': s['trace_id'], 'disposition': 'pending', 'candidate_ids': [], 'reason': ''}
                       for s in manifest['sources']]}


def check(directory, report_path, candidates_path):
    root, manifest = load_batch(directory)
    report, mined = json.loads(Path(report_path).read_text()), json.loads(Path(candidates_path).read_text())
    require(report.get('schema_version') == 'model.trace-batch-report.v1', 'unsupported batch report')
    require(report.get('batch_manifest_sha256') == sha256_file(root / 'manifest.json'), 'batch manifest changed')
    require(mined.get('schema_version') == 'model.trace-mining.v1', 'unsupported candidates manifest')
    sources = {s['trace_id']: s for s in manifest['sources']}
    by_directory = {s['source']['normalized_dir']: s for s in manifest['sources']}
    require(len(by_directory) == len(sources), 'source directories must identify distinct traces')
    for source in manifest['sources']:
        descriptor = source['source']
        path = Path(descriptor['normalized_dir'])
        require(sha256_file(path / 'normalized_trace.jsonl') == descriptor['normalized_trace_sha256']
                and sha256_file(path / 'session_manifest.json') == source['session_manifest_sha256'], 'source changed')
    if manifest.get('storage_mode') == 'references':
        require(not manifest['packets'], 'reference batch cannot declare materialized packets')
        catalogue = json.loads((root / 'catalogue.json').read_text())
        require(hashlib.sha256(canonical(catalogue)).hexdigest() == manifest['catalogue_sha256'], 'catalogue changed')
    else:
        require(sha256_file(root / 'content.sqlite3') == manifest['content_database_sha256'], 'batch database changed')
    for info in manifest['packets']:
        require(sha256_file(child(root, info['path'])) == info['sha256'], 'packet bytes changed')
    # Validate even unused top-level descriptors, including manifests with zero candidates.
    for descriptor in all_sources(mined):
        source = by_directory.get(descriptor['normalized_dir'])
        require(source is not None and descriptor == source['source'], 'manifest references foreign or changed source')
    members = {identity: set() for identity in sources}
    ids = []
    for candidate in mined.get('candidates', []):
        identity = candidate.get('candidate_id')
        require(isinstance(identity, str) and identity and identity not in ids, 'duplicate or missing candidate id')
        ids.append(identity)
        draft = child(Path(candidates_path).parent, candidate['draft_path'])
        require(draft.is_file(), 'candidate draft absent')
        families = set()
        for descriptor in candidate_sources(mined, candidate):
            source = by_directory.get(descriptor['normalized_dir'])
            require(source is not None and descriptor == source['source'], 'candidate references foreign or changed source')
            members[source['trace_id']].add(identity)
            families.add(source['source_family'])
        if 'reproduce_count' in candidate:
            count = candidate['reproduce_count']
            require(type(count) is int and 1 <= count <= len(families), 'same-family copies are not independent reproductions')
    rows = report.get('traces')
    require(isinstance(rows, list) and Counter(r.get('trace_id') for r in rows) == Counter(sources.keys()),
            'each input trace must have exactly one outcome')
    counts = Counter()
    for row in rows:
        status = row.get('disposition')
        require(status in {'mined', 'no_knowledge', 'out_of_scope', 'deferred'}, 'unprocessed trace remains')
        declared = row.get('candidate_ids')
        require(isinstance(declared, list) and len(declared) == len(set(declared))
                and set(declared) == members[row['trace_id']], 'trace/candidate membership differs')
        require(status == 'mined' and bool(declared) or status == 'deferred' and bool(row.get('reason'))
                or status in {'no_knowledge', 'out_of_scope'} and not declared and bool(row.get('reason')),
                'outcome lacks candidates or a zero/deferred reason')
        if 'deferred_stage' in row:
            require(status == 'deferred' and row['deferred_stage'] in {'unread', 'missing_evidence', 'needs_review'},
                    'invalid deferred stage')
        counts[status] += 1
    return {'ok': True, 'traces': len(rows), 'candidates': len(ids), 'outcomes': dict(counts),
            'deferred_stages': dict(Counter(r.get('deferred_stage', 'unspecified')
                                           for r in rows if r['disposition'] == 'deferred')),
            'all_targets_resolved': counts['deferred'] == 0, 'semantic_or_independent_review_pass': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['normalize', 'prepare']:
        cmd = sub.add_parser(name)
        cmd.add_argument('input', type=Path)
        cmd.add_argument('--output', type=Path, required=True)
        if name == 'normalize':
            cmd.add_argument('--redaction-policy', type=Path)
        if name == 'prepare':
            cmd.add_argument('--packet-bytes', type=int, default=262144)
            cmd.add_argument('--chunk-characters', type=int, default=8192)
            cmd.add_argument('--references-only', action='store_true',
                             help='bind sources and write previews without materializing full text or packets')
    cmd = sub.add_parser('packet')
    cmd.add_argument('batch', type=Path)
    cmd.add_argument('--number', type=int, required=True)
    cmd = sub.add_parser('event')
    cmd.add_argument('batch', type=Path)
    cmd.add_argument('--trace-id', required=True)
    cmd.add_argument('--sequence', type=int, required=True)
    cmd.add_argument('--offset', type=int, default=0)
    cmd.add_argument('--characters', type=int, default=12000)
    cmd = sub.add_parser('report-template')
    cmd.add_argument('batch', type=Path)
    cmd = sub.add_parser('check')
    cmd.add_argument('batch', type=Path)
    cmd.add_argument('--report', type=Path, required=True)
    cmd.add_argument('--candidates-manifest', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'normalize':
            result = normalize_batch(args.input, args.output,
                                     json.loads(args.redaction_policy.read_text()) if args.redaction_policy else None)
        elif args.command == 'prepare':
            result = prepare(args.input, args.output, args.packet_bytes, args.chunk_characters, args.references_only)
        elif args.command == 'packet':
            result = packet(args.batch, args.number)
        elif args.command == 'event':
            result = event(args.batch, args.trace_id, args.sequence, args.offset, args.characters)
        elif args.command == 'report-template':
            result = template(args.batch)
        else:
            result = check(args.batch, args.report, args.candidates_manifest)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
