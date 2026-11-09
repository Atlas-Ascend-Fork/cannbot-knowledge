#!/usr/bin/env python3
"""Read selected normalized evidence in exact, bounded local pages (no LLM)."""

import argparse
import json
from pathlib import Path


def events(directory):
    with (Path(directory) / 'normalized_trace.jsonl').open(encoding='utf-8') as handle:
        for line in handle:
            yield json.loads(line)


def read_event(directory, sequence, offset=0, characters=6000):
    if sequence < 1 or not 1 <= characters <= 12000:
        raise ValueError('sequence must be positive and page size must be 1..12000')
    for event in events(directory):
        if event['sequence'] != sequence:
            continue
        text = event['content']['text']
        if not 0 <= offset <= len(text):
            raise ValueError('offset is outside the original event')
        end = min(len(text), offset + characters)
        selected = text[offset:end]
        return {**{key: event[key] for key in ('outcome', 'result_metadata', 'limitations', 'session_id',
                                              'parent_session_id', 'message_id', 'parent_message_id') if key in event},
                'sequence': sequence, 'actor': event['actor'], 'event_type': event['event_type'],
                'tool': event.get('tool'), 'provenance': event['provenance'],
                'offset': offset, 'next_offset': end, 'total_characters': len(text),
                'complete_event': offset == 0 and end == len(text), 'has_more': end < len(text),
                'text_parts': [selected[start:start + 240] for start in range(0, len(selected), 240)]}
    raise ValueError('requested event does not exist')


def batch(directory, sequence=1, offset=0, characters=6000):
    """Read consecutive exact event pages under a serialized UTF-8 byte budget."""
    if sequence < 1 or offset < 0 or not 1 <= characters <= 12000:
        raise ValueError('invalid batch cursor or character budget')
    pages = []
    consumed = 0
    next_sequence, next_offset = sequence, offset
    found = False
    for event in events(directory):
        if event['sequence'] < sequence:
            continue
        if not found and event['sequence'] != sequence:
            raise ValueError('requested batch event does not exist')
        found = True
        text = event['content']['text']
        start = offset if event['sequence'] == sequence else 0
        if start > len(text):
            raise ValueError('offset is outside the original event')
        available = min(len(text) - start, characters - consumed)
        if (available == 0 and start < len(text)) or len(pages) == 50:
            return {'pages': pages, 'next_sequence': event['sequence'], 'next_offset': start, 'has_more': True}

        def page(size):
            end = start + size
            selected = text[start:end]
            return {**{key: event[key] for key in ('outcome', 'result_metadata', 'limitations', 'session_id',
                                                  'parent_session_id', 'message_id', 'parent_message_id') if key in event},
                    'sequence': event['sequence'], 'actor': event['actor'], 'event_type': event['event_type'],
                    'tool': event.get('tool'), 'provenance': event['provenance'],
                    'offset': start, 'next_offset': end, 'total_characters': len(text),
                    'complete_event': start == 0 and end == len(text), 'has_more': end < len(text),
                    'text_parts': [selected[index:index + 240] for index in range(0, len(selected), 240)]}

        def fits(candidate):
            trial = {'pages': [*pages, candidate], 'next_sequence': event['sequence'] + 1,
                     'next_offset': candidate['next_offset'], 'has_more': True}
            return len(json.dumps(trial, ensure_ascii=False, indent=2).encode('utf-8')) < 23900

        low, high = 0, available
        if not fits(page(0)):
            if pages:
                return {'pages': pages, 'next_sequence': event['sequence'], 'next_offset': start, 'has_more': True}
            raise ValueError('event metadata exceeds the bounded reader output')
        while low < high:
            middle = (low + high + 1) // 2
            if fits(page(middle)):
                low = middle
            else:
                high = middle - 1
        if low == 0 and start < len(text):
            if pages:
                return {'pages': pages, 'next_sequence': event['sequence'], 'next_offset': start, 'has_more': True}
            raise ValueError('event text cannot fit in bounded reader output')
        selected = page(low)
        pages.append(selected)
        consumed += low
        next_sequence = event['sequence'] + 1 if selected['next_offset'] == len(text) else event['sequence']
        next_offset = 0 if next_sequence > event['sequence'] else selected['next_offset']
        if selected['has_more']:
            return {'pages': pages, 'next_sequence': next_sequence, 'next_offset': next_offset, 'has_more': True}
    if not found and sequence != 1:
        raise ValueError('requested batch event does not exist')
    return {'pages': pages, 'next_sequence': next_sequence, 'next_offset': next_offset, 'has_more': False}


def index(directory, start=1, count=100):
    if start < 1 or not 1 <= count <= 100:
        raise ValueError('index start must be positive and count must be 1..100')
    selected = []
    has_more = False
    for event in events(directory):
        if event['sequence'] < start:
            continue
        if len(selected) == count:
            has_more = True
            break
        selected.append({'sequence': event['sequence'], 'actor': event['actor'],
                         'event_type': event['event_type'], 'tool': event.get('tool'),
                         **{key: event[key] for key in ('outcome', 'limitations') if key in event},
                         'text_characters': len(event['content']['text'])})
    return {'events': selected, 'next_sequence': selected[-1]['sequence'] + 1 if selected else start,
            'has_more': has_more}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['index', 'read', 'batch'])
    parser.add_argument('normalized_dir', type=Path)
    parser.add_argument('--sequence', type=int)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--characters', type=int, default=6000)
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--count', type=int, default=100)
    args = parser.parse_args()
    if args.command == 'read':
        if args.sequence is None:
            parser.error('--sequence is required for read')
        result = read_event(args.normalized_dir, args.sequence, args.offset, args.characters)
    elif args.command == 'batch':
        result = batch(args.normalized_dir, 1 if args.sequence is None else args.sequence, args.offset, args.characters)
    else:
        result = index(args.normalized_dir, args.start, args.count)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
