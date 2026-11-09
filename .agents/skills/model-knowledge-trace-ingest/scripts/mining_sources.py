"""Resolve candidate-local sources without changing evidence anchor numbering."""

import copy


CURATION = 'model.trace-curation.v1'


def descriptor(value):
    keys = ('normalized_dir', 'raw_source_sha256', 'normalized_trace_sha256')
    if not isinstance(value, dict) or any(not isinstance(value.get(key), str) or not value[key] for key in keys):
        raise ValueError('mining source must contain normalized_dir and both actual source hashes')
    return value


def candidate_sources(manifest, candidate):
    """Accept descriptors or explicit references to this manifest's source array."""
    if not isinstance(candidate, dict) or not isinstance(candidate.get('sources'), list) or not candidate['sources']:
        raise ValueError('each mining candidate requires a nonempty sources array')
    top = manifest.get('sources')
    if not isinstance(top, list):
        raise ValueError('mining manifest sources must be an array')
    result = []
    for source in candidate['sources']:
        if type(source) is int:
            if not 0 <= source < len(top):
                raise ValueError('candidate source index is outside its original mining manifest')
            source = top[source]
        result.append(descriptor(source))
    return result


def all_sources(manifest):
    sources, candidates = manifest.get('sources'), manifest.get('candidates')
    if not isinstance(sources, list) or not isinstance(candidates, list):
        raise ValueError('mining manifest sources and candidates must be arrays')
    return ([descriptor(source) for source in sources]
            + [source for candidate in candidates for source in candidate_sources(manifest, candidate)])


def preserve_candidate(candidate, manifest, decision):
    """Stage one semantic decision without rewriting claims, anchors or comparison data."""
    allowed = {'candidate_id', 'status', 'operation', 'target_path', 'expected_target_sha256',
               'dedup', 'reproduce_count', 'reason', 'omit_claims', 'scope_evidence', 'validation_scope'}
    if not isinstance(decision, dict) or set(decision) - allowed:
        raise ValueError('unknown curation decision fields; revise the mining candidate explicitly')
    if candidate.get('candidate_id') != decision.get('candidate_id'):
        raise ValueError('decision identity differs from mining candidate')
    identity = candidate['candidate_id']
    status = decision.get('status')
    if status in {'deferred', 'rejected'}:
        if not isinstance(decision.get('reason'), str) or not decision['reason'].strip():
            raise ValueError('unaccepted candidate needs a reason')
        return {'candidate_id': identity, 'source_candidate_ids': [identity],
                'status': status, 'reason': decision['reason']}
    if (status, decision.get('operation')) not in {('published', 'new'), ('merged', 'merge')}:
        raise ValueError('invalid accepted status/operation')
    entry = copy.deepcopy(candidate)
    # Source indices belong to the original manifest; all other evidence is copied intact.
    entry['sources'] = copy.deepcopy(candidate_sources(manifest, candidate))
    entry.update({k: copy.deepcopy(v) for k, v in decision.items() if k != 'omit_claims'})
    entry['source_candidate_ids'] = [identity]
    claims = entry.get('claims')
    if not isinstance(claims, list) or not claims:
        raise ValueError('accepted candidate needs claims')
    ids = [c.get('id') for c in claims]
    if any(not isinstance(cid, str) or not cid for cid in ids) or len(set(ids)) != len(ids):
        raise ValueError('invalid original claim identities')
    omitted = {}
    for item in decision.get('omit_claims', []):
        cid = item.get('claim_id')
        if cid not in ids or cid in omitted or not str(item.get('reason', '')).strip():
            raise ValueError('omitted claim needs a unique original identity and reason')
        omitted[cid] = item['reason']
    entry['claim_dispositions'] = [
        {'candidate_id': identity, 'claim_id': cid, 'action': 'omitted', 'reason': reason}
        for cid, reason in omitted.items()]
    entry['claims'] = [c for c in claims if c['id'] not in omitted]
    if not entry['claims']:
        raise ValueError('all claims omitted; defer or reject the candidate')
    artifacts = copy.deepcopy(candidate.get('mechanism_artifacts', []))
    kept = []
    for artifact in artifacts:
        artifact['claim_ids'] = [cid for cid in artifact.get('claim_ids', []) if cid not in omitted]
        if artifact['claim_ids']:
            kept.append({**artifact, 'verbatim_verified': False})
    entry.pop('mechanism_artifacts', None)
    entry['evidence_audit'] = {'result': 'pending', 'mode': 'trace_snapshot',
                             'trace_snapshot': {'mechanism_artifacts': kept}}
    return entry


def check_adoption(manifest, entry, publication):
    """Reject lost evidence and ledger-only deletion; does not infer prose semantics."""
    by_id = {c['candidate_id']: c for c in manifest['candidates']}
    members = entry.get('source_candidate_ids', [entry['candidate_id']])
    decisions = {}
    for item in entry.get('claim_dispositions', []):
        key = (item.get('candidate_id'), item.get('claim_id'))
        if key in decisions or item.get('action') != 'omitted' or not str(item.get('reason', '')).strip():
            raise ValueError('claim disposition needs a unique omitted identity and reason')
        decisions[key] = item
    used_decisions = set()
    used_claims = set()
    for member in members:
        original = by_id[member]
        adopted_mapping = {}
        original_comparison = original.get('performance_comparison')
        actual_comparison = (entry.get('performance_comparisons', {}).get(member)
                             if len(members) > 1 else entry.get('performance_comparison'))
        if original.get('performance_comparison') is not None:
            if bound_evidence(original_comparison, candidate_sources(manifest, original)) != bound_evidence(
                    actual_comparison, entry.get('sources', [])):
                raise ValueError('mining performance comparison changed or lost')
        # Old identity-only manifests remain readable; evidence-bearing candidates are strict.
        for claim in original.get('claims', []):
            key = (member, claim['id'])
            if key in decisions:
                if claim['text'] in publication:
                    raise ValueError('omitted claim remains in title, description or body: ' + str(key))
                used_decisions.add(key)
                continue
            matches = [c for c in entry.get('claims', []) if
                       (len(members) == 1 and c['id'] == claim['id']) or
                       {'candidate_id': member, 'claim_id': claim['id']} in c.get('source_claims', [])]
            if len(matches) != 1:
                raise ValueError('original claim lacks adoption or explicit omission: ' + str(key))
            adopted = matches[0]
            used_claims.add(adopted['id'])
            adopted_mapping[claim['id']] = adopted['id']
            # A same-id rewrite must be a new mining revision, not an untracked curation repair.
            for field, value in claim.items():
                if field == 'id' and len(members) > 1:
                    continue
                expected = bound_evidence(value, candidate_sources(manifest, original)) if field in {'anchors', 'signals'} else value
                actual = bound_evidence(adopted.get(field), entry.get('sources', [])) if field in {'anchors', 'signals'} else adopted.get(field)
                if actual != expected:
                    raise ValueError('mining claim field changed or lost: ' + str(key) + '.' + field)
            if claim.get('kind') == 'performance_gain':
                if original.get('performance_comparison') is None:
                    raise ValueError('original performance gain lacks paired comparison')
                if actual_comparison is None:
                    raise ValueError('mining performance comparison changed or lost')
        for artifact in original.get('mechanism_artifacts', []):
            mapped_ids = {adopted_mapping[cid] for cid in artifact.get('claim_ids', []) if cid in adopted_mapping}
            if not mapped_ids:
                continue
            staged = entry.get('evidence_audit', {}).get('trace_snapshot', {}).get('mechanism_artifacts', [])
            original_anchors = bound_evidence(artifact.get('anchors'), candidate_sources(manifest, original))
            if not any(a.get('text') == artifact.get('text') and mapped_ids <= set(a.get('claim_ids', []))
                       and bound_evidence(a.get('anchors'), entry.get('sources', [])) == original_anchors for a in staged):
                raise ValueError('complete mining mechanism artifact changed or lost; re-mine the source unit')
    if set(decisions) != used_decisions:
        raise ValueError('claim disposition references a foreign claim')
    if any(by_id[m].get('claims') for m in members):
        if used_claims != {c['id'] for c in entry.get('claims', [])}:
            raise ValueError('ledger introduces claims absent from the bound mining manifest')


def bound_evidence(value, sources):
    """Compare local anchors by their immutable source identity, including explicit merges."""
    if isinstance(value, list):
        return [bound_evidence(item, sources) for item in value]
    if isinstance(value, dict):
        if {'source', 'sequence'} <= value.keys():
            index = value['source']
            if type(index) is not int or not 0 <= index < len(sources):
                raise ValueError('invalid comparison source anchor')
            return {**value, 'source': descriptor(sources[index])}
        return {key: bound_evidence(item, sources) for key, item in value.items()}
    return value
