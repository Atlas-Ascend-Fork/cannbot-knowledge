#!/usr/bin/env python3
"""Validate model-specific evidence, source bindings and staged Runbook bytes."""

import argparse
from collections import Counter, OrderedDict
import json
import math
from pathlib import Path
import re
import sys

from normalize_trace import verify
from model_trace_common import REPOSITORY, child, sha256_file, write_new_json
from mining_sources import CURATION, check_adoption
from trace_privacy import require_publication_clean

sys.path.insert(0, str(REPOSITORY))
from governance.contracts.knowledge import Contract, split_frontmatter


ROLE_SETS = {
    'repair_recipe': {'failure', 'before', 'after', 'validation'},
    'diagnostic_rule': {'trigger', 'probe', 'observation', 'discrimination'},
    'negative_result': {'attempt', 'failure', 'boundary'},
    'validated_pattern': {'implementation', 'validation'},
}
OBJECTIVE = {'tool_result', 'metric', 'artifact', 'error'}
WORKLOAD = {'model', 'hardware', 'precision', 'input_tokens', 'output_tokens',
            'batch_or_concurrency', 'parallelism', 'measurement'}
SECTIONS = {'适用场景', '触发与观测', '探针与操作', '机制与判别', '验证信号', '适用与失效边界'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def event_texts(event):
    text = event.get('content', {}).get('text', '')
    texts = [text]
    def walk(value):
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    try:
        walk(json.loads(text))
    except ValueError:
        pass
    return texts


def validate(ledger_path, cards_root, route, approved=False, repository=REPOSITORY,
             candidates_manifest=None, collect_errors=False):
    ledger = json.loads(Path(ledger_path).read_text(encoding='utf-8'))
    require(ledger.get('schema_version') == 'model.trace-ledger.v1', 'unsupported model ledger')
    contract = Contract(repository)
    require(route in contract.scopes and 'model' in contract.scopes[route]['domains'], 'invalid model route')
    require(ledger.get('route') == route, 'ledger route differs from requested route')
    require(isinstance(ledger.get('entries'), list), 'entries must be a list')
    require(ledger.get('curation_contract', CURATION) == CURATION, 'unsupported curation contract')
    require(ledger.get('curation_contract') != CURATION or candidates_manifest is not None,
            'curation requires the original mining manifest')
    mining_manifest = None
    batch_sources = None
    if 'batch_manifest' in ledger:
        binding = ledger['batch_manifest']
        require(isinstance(binding, dict) and isinstance(binding.get('path'), str), 'invalid batch manifest binding')
        batch_path = Path(binding['path'])
        require(batch_path.is_absolute() and batch_path.name == 'manifest.json', 'invalid batch input path')
        require(binding.get('sha256') == sha256_file(batch_path), 'batch input manifest changed')
        batch = json.loads(batch_path.read_text())
        require(batch.get('schema_version') == 'model.trace-batch.v1', 'unsupported batch input')
        batch_sources = {s['source']['normalized_dir']: s for s in batch['sources']}
        require(len(batch_sources) == len(batch['sources']), 'duplicate batch source directory')
    if candidates_manifest is not None:
        require(ledger.get('candidates_manifest_sha256') == sha256_file(candidates_manifest),
                'candidate manifest hash changed or is missing')
        manifest = json.loads(Path(candidates_manifest).read_text(encoding='utf-8'))
        mining_manifest = manifest
        require(manifest.get('schema_version') == 'model.trace-mining.v1', 'unsupported mining manifest')
        candidates = manifest.get('candidates')
        require(isinstance(candidates, list), 'mining manifest requires candidates')
        candidate_ids = []
        expected = []
        for candidate in candidates:
            identity = candidate.get('candidate_id')
            candidate_route = candidate.get('route')
            require(isinstance(identity, str) and bool(identity), 'mining candidate lacks identity')
            require(candidate_route in contract.scopes and 'model' in contract.scopes[candidate_route]['domains'],
                    'mining candidate requires a registered model route')
            candidate_ids.append(identity)
            if candidate_route == route:
                expected.append(identity)
        require(len(set(candidate_ids)) == len(candidate_ids), 'duplicate mining candidate identity')
        actual = []
        for entry in ledger['entries']:
            members = entry.get('source_candidate_ids', [entry.get('candidate_id')])
            require(isinstance(members, list) and bool(members) and all(isinstance(item, str) for item in members),
                    'ledger entry lacks source candidate identities')
            actual.extend(members)
        require(Counter(actual) == Counter(expected),
                'ledger must account for every input candidate exactly once for this route')
    reconstruction_path = Path(ledger_path).parent / 'reconstruction.json'
    require(ledger.get('reconstruction_sha256') == sha256_file(reconstruction_path),
            'reconstruction content hash changed or is missing')
    reconstruction = json.loads(reconstruction_path.read_text(encoding='utf-8'))
    require(reconstruction.get('schema_version') == 'model.trace-reconstruction.v1'
            and reconstruction.get('route') == route, 'invalid model reconstruction')
    reconstructions = reconstruction.get('traces')
    require(isinstance(reconstructions, list), 'reconstruction requires per-source traces')
    source_cache = OrderedDict()
    source_versions = {}

    def load_source(source):
        key = (source['normalized_dir'], source.get('raw_source_sha256'), source.get('normalized_trace_sha256'))
        if key in source_cache:
            source_cache.move_to_end(key)
            return source_cache[key][0], source_cache[key][1]
        root = Path(source['normalized_dir'])
        require(root.is_absolute(), 'normalized_dir must be absolute')
        require(verify(root)['ok'], 'normalized trace failed verification')
        session_path = root / 'session_manifest.json'
        session = json.loads(session_path.read_text())
        raw_hash = source.get('raw_source_sha256', '')
        require(bool(re.fullmatch('[0-9a-f]{64}', raw_hash)), 'invalid raw source hash')
        require(raw_hash == session['source']['sha256'], 'raw source hash differs from manifest')
        require(source.get('normalized_trace_sha256') == sha256_file(root / 'normalized_trace.jsonl'),
                'normalized content hash changed')
        with (root / 'normalized_trace.jsonl').open() as handle:
            source_events = {event['sequence']: event for event in map(json.loads, handle)}
        session_hash = sha256_file(session_path)
        require(key not in source_versions or source_versions[key] == session_hash,
                'normalized source changed during validation')
        source_versions[key] = session_hash
        source_cache[key] = (raw_hash, source_events)
        if len(source_cache) > 4:
            source_cache.popitem(last=False)
        return raw_hash, source_events

    targets = set()
    identities = set()
    accepted = 0
    errors = []
    for entry in ledger['entries']:
        try:
            identity = entry.get('candidate_id')
            require(identity and identity not in identities, 'candidate id is absent or duplicated')
            identities.add(identity)
            status = entry.get('status')
            require(status in {'published', 'merged', 'deferred', 'rejected'}, 'invalid candidate status')
            if status not in {'published', 'merged'}:
                require(bool(entry.get('reason')), 'unaccepted candidate lacks a reason')
                continue
            target = entry.get('target_path', '')
            require(target not in targets, 'duplicate target')
            targets.add(target)
            relative = Path(target)
            require(len(relative.parts) == 2 and relative.parts[0] in contract.runbook_areas,
                    'target requires registered area and slug')
            require(relative.name != 'index.md', 'index cannot be a card')
            staged = child(cards_root, target)
            require(staged.is_file(), 'staged target is missing')
            publication = staged.read_text(encoding='utf-8')
            require_publication_clean(publication)
            metadata, body = split_frontmatter(publication)
            require(metadata is not None, 'missing frontmatter')
            issues = contract.validate_card(Path('knowledge/model') / route / 'runbooks' / relative, metadata, body)
            require(not issues, 'machine contract: ' + '; '.join(issue.code + ': ' + issue.message for issue in issues[:8]))
            headings = set(re.findall(r'^## (.+)$', body, re.M))
            require(SECTIONS <= headings, 'missing model Runbook sections')
            operation = entry.get('operation')
            require((status, operation) in {('published', 'new'), ('merged', 'merge')}, 'invalid status/operation')
            if operation == 'merge':
                require(bool(re.fullmatch('[0-9a-f]{64}', entry.get('expected_target_sha256', ''))),
                        'merge requires expected target hash')
            dedup = entry.get('dedup') or {}
            require(dedup.get('decision') in {'create', 'update', 'merge'} and dedup.get('queries'),
                    'missing Query dedup decision')
            form = entry.get('knowledge_form')
            require(form in ROLE_SETS, 'unknown knowledge form')
            sources = entry.get('sources') or []
            require(bool(sources), 'accepted candidate has no sources')
            events = []
            raw_hashes = set()
            for source in sources:
                raw_hash, source_events = load_source(source)
                raw_hashes.add(raw_hash)
                events.append(source_events)
                matching = [trace for trace in reconstructions
                            if trace.get('source') == source]
                require(len(matching) == 1, 'source lacks a unique reconstruction')
                trace = matching[0]
                require(bool((trace.get('task') or {}).get('summary'))
                        and isinstance(trace.get('environment'), dict), 'missing reconstructed task or environment')
                for field in ('timeline', 'facts', 'assumptions', 'unknowns', 'limitations'):
                    require(isinstance(trace.get(field), list), 'missing reconstruction ' + field)
                require(bool(trace['timeline']) and bool(trace['facts']), 'reconstruction has no timeline or facts')
                coverage = trace.get('coverage') or {}
                require(coverage.get('indexed_sequence_range') == [1, len(events[-1])],
                        'reconstruction event coverage differs from trace')
                ranges = coverage.get('semantic_review_ranges')
                require(isinstance(ranges, list) and bool(ranges), 'missing semantic review ranges')
                for span in ranges:
                    require(isinstance(span, list) and len(span) == 2 and
                            all(type(number) is int for number in span) and
                            1 <= span[0] <= span[1] <= len(events[-1]), 'invalid semantic review range')
                for item in trace['timeline'] + trace['facts']:
                    require(bool(item.get('event_refs')) and
                            all(type(seq) is int and seq in events[-1] for seq in item['event_refs']),
                            'reconstruction has an invalid event reference')
            count = entry.get('reproduce_count')
            require(type(count) is int and 1 <= count <= len(raw_hashes), 'unsupported independent reproduction count')
            if batch_sources is not None:
                families = set()
                for source in sources:
                    original = batch_sources.get(source['normalized_dir'])
                    require(original is not None and source == original['source'], 'source is outside the input batch')
                    require(bool(original.get('source_family')), 'batch source family is absent')
                    families.add(original['source_family'])
                require(count <= len(families), 'same-family copies are not independent reproductions')
            def resolve(anchors):
                require(isinstance(anchors, list) and bool(anchors), 'missing evidence anchors')
                resolved = []
                for anchor in anchors:
                    index, sequence = anchor.get('source'), anchor.get('sequence')
                    require(type(index) is int and 0 <= index < len(events), 'invalid source anchor')
                    require(type(sequence) is int and sequence in events[index], 'invalid sequence anchor')
                    event = events[index][sequence]
                    provenance = event.get('provenance') or {}
                    require(bool(provenance.get('raw_source')) and type(provenance.get('raw_record')) is int
                            and provenance['raw_record'] >= 1
                            and bool(re.fullmatch('[0-9a-f]{64}', provenance.get('raw_sha256', ''))),
                            'anchor lacks raw record provenance')
                    resolved.append(event)
                return resolved
            roles = entry.get('evidence_roles') or {}
            require(ROLE_SETS[form] <= set(roles), 'missing form-specific evidence role')
            for anchors in roles.values():
                resolve(anchors)
            if form in {'repair_recipe', 'validated_pattern'}:
                for event in resolve(roles['validation']):
                    outcome = event.get('outcome') or {}
                    require(event['event_type'] in {'tool_result', 'metric', 'artifact'}
                            and not outcome.get('failed') and not outcome.get('output_truncated')
                            and not event.get('limitations') and outcome.get('exit_code', 0) == 0,
                            'failed, truncated or ambiguous execution cannot validate a successful pattern')
            if ledger.get('curation_contract') == CURATION:
                relation = entry.get('scope_evidence') or {}
                require(bool(str(relation.get('summary', '')).strip()), 'missing actual model/framework relation')
                relation_events = resolve(relation.get('anchors'))
                require(any(event['event_type'] in OBJECTIVE for event in relation_events),
                        'model/framework relation lacks observed integration or environment evidence')
                levels = entry.get('validation_scope')
                require(isinstance(levels, list) and bool(levels) and set(levels) <= {
                    'source_read', 'static_check', 'cpu_reference', 'device_functional', 'end_to_end', 'performance'},
                    'missing or invalid validation scope')
            if mining_manifest is not None:
                check_adoption(mining_manifest, entry, '\n'.join(
                    [metadata.get('title', ''), metadata.get('description', ''), body]))
            claims = entry.get('claims') or []
            require(bool(claims), 'accepted candidate has no adopted claims')
            comparisons = entry.get('performance_comparisons', {})
            require(isinstance(comparisons, dict), 'performance comparisons must map source candidate identities')
            require(set(comparisons) <= set(entry.get('source_candidate_ids', [identity])),
                    'performance comparison references a foreign candidate')
            require(not (comparisons and entry.get('performance_comparison') is not None),
                    'use either a single comparison or member comparisons')
            claim_ids = set()
            for claim in claims:
                require(claim.get('id') and claim['id'] not in claim_ids, 'invalid or duplicate claim id')
                claim_ids.add(claim['id'])
                require(bool(claim.get('text')) and claim['text'] in body, 'adopted claim is absent from card')
                resolve(claim.get('anchors'))
                signals = resolve(claim.get('signals'))
                require(all(event['event_type'] in OBJECTIVE for event in signals), 'signal is not an objective observation')
                if claim.get('kind') == 'performance_gain':
                    if comparisons:
                        origins = claim.get('source_claims') or []
                        require(bool(origins) and all(origin.get('candidate_id') in comparisons for origin in origins),
                                'merged performance gain lacks paired member comparison')
                    else:
                        require(entry.get('performance_comparison') is not None, 'performance gain lacks paired comparison')
            audit = entry.get('evidence_audit') or {}
            require(audit.get('mode') == 'trace_snapshot', 'model producer requires trace_snapshot')
            require(audit.get('result') == ('pass' if approved else 'pending'), 'incorrect review approval state')
            artifacts = audit.get('trace_snapshot', {}).get('mechanism_artifacts') or []
            require(bool(artifacts), 'missing verbatim mechanism artifact')
            mapped = set()
            for artifact_index, artifact in enumerate(artifacts):
                text = artifact.get('text', '')
                require(bool(text.strip()) and text in body, 'mechanism artifact absent from card')
                refs = resolve(artifact.get('anchors'))
                require(any(text in content for event in refs for content in event_texts(event)),
                        'mechanism artifact #' + str(artifact_index) + ' for ' + str(artifact.get('claim_ids')) +
                        ' is not verbatim in anchored sequences ' + str([anchor.get('sequence') for anchor in artifact.get('anchors', [])]) +
                        '; retain original tool line numbers, prefixes, indentation and complete code unit; do not reformat or synthesize code')
                require(artifact.get('verbatim_verified') is approved, 'incorrect verbatim approval state')
                ids = set(artifact.get('claim_ids') or [])
                require(bool(ids) and ids <= claim_ids, 'artifact references nonexistent claim')
                mapped.update(ids)
            require(mapped == claim_ids, 'claim lacks mechanism artifact mapping')
            paired = list(comparisons.values())
            if entry.get('performance_comparison') is not None:
                paired.append(entry['performance_comparison'])
            for comparison in paired:
                baseline, candidate = comparison['baseline'], comparison['candidate']
                for sample in (baseline, candidate):
                    workload = sample.get('workload') or {}
                    require(WORKLOAD <= set(workload), 'performance workload is incomplete')
                    require(all(str(workload[key]).strip().lower() not in {'', 'unknown', 'none'} for key in WORKLOAD),
                            'performance workload is unknown')
                    require(all(event['event_type'] in OBJECTIVE for event in resolve(sample.get('signals'))),
                            'performance sample lacks objective signals')
                    metric = sample['metric']
                    require(all(metric.get(key) for key in ('name', 'unit', 'aggregation')), 'incomplete performance metric')
                    value = metric.get('value')
                    require(type(value) in {int, float} and math.isfinite(value), 'nonfinite performance result')
                require(all(baseline['workload'][key] == candidate['workload'][key] for key in WORKLOAD),
                        'performance workloads are not comparable')
                require(all(baseline['metric'][key] == candidate['metric'][key]
                            for key in ('name', 'unit', 'aggregation')), 'performance metric definitions differ')
            accepted += 1
        except (ValueError, KeyError, TypeError, OSError) as error:
            if not collect_errors:
                raise
            errors.append({'candidate_id': entry.get('candidate_id'), 'target_path': entry.get('target_path'),
                           'error': str(error)})
    for (directory, _, trace_hash), session_hash in source_versions.items():
        root = Path(directory)
        try:
            require(sha256_file(root / 'normalized_trace.jsonl') == trace_hash and
                    sha256_file(root / 'session_manifest.json') == session_hash,
                    'normalized source changed during validation')
        except (ValueError, OSError) as error:
            if not collect_errors:
                raise
            errors.append({'scope': 'source', 'error': str(error)})
    actual = {path.relative_to(cards_root).as_posix() for path in Path(cards_root).rglob('*.md')}
    if actual != targets:
        if not collect_errors:
            raise ValueError('staged cards and accepted targets differ')
        errors.append({'scope': 'inventory', 'error': 'staged cards and accepted targets differ'})
    result = {'ok': not errors, 'accepted': accepted, 'total': len(ledger['entries']), 'route': route}
    if errors:
        result['errors'] = errors
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', type=Path)
    parser.add_argument('cards_root', type=Path)
    parser.add_argument('--route', required=True)
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--candidates-manifest', type=Path)
    parser.add_argument('--fail-fast', action='store_true', help='stop at the first candidate error')
    parser.add_argument('--report', type=Path, help='create a full error report; console output stays bounded')
    args = parser.parse_args()
    try:
        result = validate(args.ledger, args.cards_root, args.route, args.approved,
                          candidates_manifest=args.candidates_manifest, collect_errors=not args.fail_fast)
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'ok': False, 'error': str(error), 'errors': [{'scope': 'batch', 'error': str(error)}]}
    if args.report:
        try:
            write_new_json(args.report, result)
        except (ValueError, OSError) as error:
            print(json.dumps({'ok': False, 'error': str(error)}))
            return 1
        print(json.dumps({'ok': result['ok'], 'accepted': result.get('accepted', 0),
                          'errors_count': len(result.get('errors', [])), 'report': str(args.report)}, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
