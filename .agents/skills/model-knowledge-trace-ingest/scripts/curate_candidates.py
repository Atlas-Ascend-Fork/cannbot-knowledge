#!/usr/bin/env python3
"""Lossless candidate promotion; curation decisions and card prose remain Agent-authored."""

import argparse
import json
from pathlib import Path

from mining_sources import CURATION, all_sources, preserve_candidate
from model_trace_common import sha256_file, write_new_json


def promote(manifest_path, decisions_path, reconstruction_path, output, route, batch_manifest=None):
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get('schema_version') != 'model.trace-mining.v1':
        raise ValueError('unsupported mining manifest')
    decisions = json.loads(Path(decisions_path).read_text())
    if not isinstance(decisions, list):
        raise ValueError('decisions must be an array')
    candidates = [c for c in manifest['candidates'] if c['route'] == route]
    expected = {c['candidate_id'] for c in candidates}
    ids = [d.get('candidate_id') for d in decisions]
    if len(expected) != len(candidates) or len(set(ids)) != len(ids) or set(ids) != expected:
        raise ValueError('decisions must cover every route candidate exactly once')
    destination = Path(output)
    if Path(reconstruction_path).resolve() != destination.parent.resolve() / 'reconstruction.json':
        raise ValueError('reconstruction must be beside the output ledger')
    by_id = {d['candidate_id']: d for d in decisions}
    entries = [preserve_candidate(c, manifest, by_id[c['candidate_id']]) for c in candidates]
    result = {'schema_version': 'model.trace-ledger.v1', 'curation_contract': CURATION, 'route': route,
              'candidates_manifest_sha256': sha256_file(manifest_path),
              'reconstruction_sha256': sha256_file(reconstruction_path), 'entries': entries}
    if batch_manifest is not None:
        result['batch_manifest'] = {'path': str(Path(batch_manifest).resolve()),
                                    'sha256': sha256_file(batch_manifest)}
    for source in all_sources(manifest):
        if destination.resolve().is_relative_to(Path(source['normalized_dir']).resolve()):
            raise ValueError('ledger output cannot be inside normalized sources')
    write_new_json(destination, result)
    return {'ok': True, 'entries': len(entries), 'output': str(destination),
            'knowledge_written': False, 'semantic_review_pass': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--reconstruction', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--route', choices=['inference', 'training', 'spatial', 'embodied'], required=True)
    parser.add_argument('--batch-manifest', type=Path)
    args = parser.parse_args()
    try:
        result = promote(args.manifest, args.decisions, args.reconstruction, args.output, args.route, args.batch_manifest)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'ok': False, 'error': str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
