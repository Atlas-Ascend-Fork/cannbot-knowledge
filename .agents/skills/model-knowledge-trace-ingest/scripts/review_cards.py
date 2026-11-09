#!/usr/bin/env python3
"""Bind an independent review to staged card bytes; never write knowledge cards."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from model_trace_common import REPOSITORY, canonical, child, sha256_file
from mining_sources import CURATION
from trace_privacy import require_publication_clean
from normalize_trace import require

REVIEW_CHECKS = {'scope', 'title', 'description', 'body', 'source_authority',
                 'validation_scope', 'comparisons', 'contradictions'}
SEMANTIC_FINDINGS = {'evidence', 'scope', 'api_contract', 'causality', 'comparison', 'validation', 'privacy'}


def subject(ledger_path, cards_root):
    ledger_path, cards_root = Path(ledger_path), Path(cards_root)
    ledger = json.loads(ledger_path.read_text())
    frozen = copy.deepcopy(ledger)
    cards = []
    for entry in frozen['entries']:
        if entry.get('status') not in {'published', 'merged'}:
            continue
        audit = entry.get('evidence_audit', {})
        audit['result'] = 'pending'
        for item in audit.get('trace_snapshot', {}).get('mechanism_artifacts', []):
            item['verbatim_verified'] = False
        target = entry['target_path']
        require_publication_clean(child(cards_root, target).read_text())
        card = {'path': target, 'sha256': sha256_file(child(cards_root, target))}
        if frozen.get('curation_contract') == CURATION:
            card.update(claim_ids=[c['id'] for c in entry.get('claims', [])],
                        artifact_indexes=list(range(len(audit.get('trace_snapshot', {}).get('mechanism_artifacts', [])))))
        cards.append(card)
    actual = {p.relative_to(cards_root).as_posix() for p in cards_root.rglob('*.md')}
    require(actual == {c['path'] for c in cards} and len(cards) == len(actual), 'staged card inventory differs')
    reconstruction = ledger_path.parent / 'reconstruction.json'
    require(sha256_file(reconstruction) == ledger['reconstruction_sha256'], 'reconstruction changed')
    fields = {'schema_version': 'model.trace-review-subject.v1',
              'ledger_sha256': hashlib.sha256(canonical(frozen)).hexdigest(),
              'reconstruction_sha256': sha256_file(reconstruction), 'cards': sorted(cards, key=lambda c: c['path'])}
    if frozen.get('curation_contract') == CURATION:
        fields.update(curation_contract=CURATION, required_checks=sorted(REVIEW_CHECKS))
    return {**fields, 'subject_sha256': hashlib.sha256(canonical(fields)).hexdigest()}


def verify(ledger_path, cards_root, receipt_path, sender):
    frozen = subject(ledger_path, cards_root)
    receipt = json.loads(Path(receipt_path).read_text())
    require(receipt.get('schema_version') == 'model.trace-review.v1', 'unsupported review receipt')
    require(receipt.get('subject') == frozen, 'review does not bind current staged bytes')
    require(isinstance(sender, str) and bool(sender.strip()) and receipt.get('reviewer') == sender,
            'reviewer differs from caller-verified runtime sender')
    require(receipt.get('attestation') == 'agent-runtime-message', 'review attestation is absent')
    require(receipt.get('verdict') == 'PASS' and receipt.get('summary'), 'independent review did not pass')
    require(isinstance(receipt.get('findings'), list), 'review findings must be a list')
    require(all(isinstance(f, dict) and f.get('severity') == 'minor' for f in receipt['findings']),
            'review has unresolved or invalid findings')
    require(not any(f.get('category') in SEMANTIC_FINDINGS for f in receipt['findings']),
            'semantic findings require revision even when labeled minor')
    if frozen.get('curation_contract') == CURATION:
        require(all(f.get('category') in {'format', 'clarity'} for f in receipt['findings']),
                'curation findings require explicit categories')
        coverage = receipt.get('coverage')
        require(isinstance(coverage, list) and len(coverage) == len(frozen['cards']),
                'review coverage must include every card')
        by_path = {row.get('path'): row for row in coverage if isinstance(row, dict)}
        require(len(by_path) == len(coverage) and set(by_path) == {c['path'] for c in frozen['cards']},
                'review coverage has duplicate or foreign cards')
        for card in frozen['cards']:
            row = by_path[card['path']]
            require(set(row.get('checked', [])) >= REVIEW_CHECKS, 'review omitted title/body or semantic checks')
            require(sorted(row.get('claim_ids', [])) == sorted(card['claim_ids']), 'review omitted adopted claims')
            require(row.get('complete_artifact_indexes') == card['artifact_indexes'],
                    'review must confirm complete mechanism units')
            require(row.get('unmapped_assertions') == [], 'review found unmapped published assertions')
    from datetime import datetime, timedelta
    # A timestamp describes the recorded review; it does not authenticate a sender.
    reviewed = datetime.fromisoformat(receipt['reviewed_at'].replace('Z', '+00:00'))
    require(reviewed.tzinfo is not None and reviewed.utcoffset() == timedelta(0), 'review timestamp must be UTC')
    return {'ok': True, 'subject_sha256': frozen['subject_sha256'], 'cards': len(frozen['cards']),
            'runtime_sender_authentication': 'caller-responsibility', 'knowledge_written': False}


def inventory(ledger_path, cards_root, changed_paths, repository=REPOSITORY):
    """Check the caller's operation-scoped diff and published bytes; never run Git."""
    ledger = json.loads(Path(ledger_path).read_text())
    expected = {}
    for entry in ledger['entries']:
        if entry.get('status') in {'published', 'merged'}:
            relative = 'knowledge/model/' + ledger['route'] + '/runbooks/' + entry['target_path']
            require_publication_clean(child(cards_root, entry['target_path']).read_text())
            expected[relative] = sha256_file(child(cards_root, entry['target_path']))
    paths = json.loads(Path(changed_paths).read_text())
    require(isinstance(paths, list) and all(isinstance(p, str) for p in paths), 'changed paths must be an array')
    require(len(set(paths)) == len(paths), 'duplicate changed path')
    actual = set()
    for name in paths:
        path = child(repository, name)
        relative = path.relative_to(Path(repository).absolute()).parts
        if len(relative) >= 5 and relative[:2] == ('knowledge', 'model') and relative[3] == 'runbooks':
            if path.suffix == '.md' and path.name != 'index.md':
                actual.add(name)
    require(actual == set(expected), 'published card changes differ from the accepted inventory')
    require(all(sha256_file(child(repository, name)) == digest for name, digest in expected.items()),
            'published card bytes differ from reviewed staging')
    return {'ok': True, 'cards': len(expected), 'knowledge_written': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['subject', 'verify', 'inventory'])
    parser.add_argument('ledger', type=Path)
    parser.add_argument('cards_root', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--sender')
    parser.add_argument('--changed-paths', type=Path)
    parser.add_argument('--repository', type=Path, default=REPOSITORY)
    args = parser.parse_args()
    if args.command == 'verify' and (not args.receipt or not args.sender):
        parser.error('verify requires --receipt and --sender from the actual runtime message')
    if args.command == 'inventory' and not args.changed_paths:
        parser.error('inventory requires --changed-paths from this operation, excluding prior WIP')
    try:
        if args.command == 'inventory':
            result = inventory(args.ledger, args.cards_root, args.changed_paths, args.repository)
        elif args.command == 'subject':
            result = subject(args.ledger, args.cards_root)
        else:
            result = verify(args.ledger, args.cards_root, args.receipt, args.sender)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'ok': False, 'error': str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get('ok') is False else 0


if __name__ == '__main__':
    raise SystemExit(main())
