#!/usr/bin/env python3
"""Validate typed re-review miner output against a rereview queue."""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROLE_SETS = {
    "repair_recipe": {"failure", "before", "repair_after", "validation_after"},
    "diagnostic_rule": {"trigger", "probe", "observation", "interpretation"},
    "negative_result": {"attempt", "observation", "boundary"},
    "validated_pattern": {"implementation", "validation"},
}
FORM_SECTIONS = {
    "repair_recipe": "## 解决配方",
    "diagnostic_rule": "## 判别方法",
    "negative_result": "## 失败路线",
    "validated_pattern": "## 完整实现",
}
ARTIFACT_KINDS = {"code", "config", "command", "output", "probe"}
RECONSTRUCTION_METHODS = {
    "full_snapshot",
    "base_plus_complete_edit_chain",
    "self_contained_event",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ANCHOR_RE = re.compile(r"^([0-9a-f]{12})#([1-9][0-9]*)$")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_sequences(path):
    sequences = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL line {line_number}: {exc}") from exc
            sequence = event.get("sequence", event.get("seq"))
            if not isinstance(sequence, int):
                raise ValueError(f"line {line_number} lacks integer sequence")
            sequences.append(sequence)
    return sequences


def session_manifest(path):
    manifest_path = path.parent / "session_manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"missing {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def check_anchor(anchor, trace_id, raw_sha, normalized_sha, last_sequence):
    match = ANCHOR_RE.fullmatch(str(anchor))
    if not match:
        return f"invalid anchor syntax {anchor!r}"
    prefix, sequence_text = match.groups()
    if not (
        str(trace_id).startswith(prefix)
        or raw_sha.startswith(prefix)
        or normalized_sha.startswith(prefix)
    ):
        return f"anchor {anchor!r} does not identify this trace snapshot"
    sequence = int(sequence_text)
    if sequence > last_sequence:
        return f"anchor {anchor!r} exceeds last sequence {last_sequence}"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queue", type=Path)
    parser.add_argument("output_roots", nargs="+", type=Path)
    parser.add_argument("--shard", type=int, action="append", help="validate only these original queue shard values")
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    allowed_shards = set(args.shard or [])
    expected = {
        index: item
        for index, item in enumerate(queue.get("items") or [])
        if not allowed_shards or item.get("shard") in allowed_shards
    }
    errors = []
    decisions = {}
    candidate_forms = Counter()
    manifests = []

    for root in args.output_roots:
        manifests.extend(sorted(root.rglob("manifest.json")))
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{manifest_path}: invalid JSON: {exc}")
            continue
        trace_id = str(manifest.get("trace_id") or manifest_path.parent.name)
        normalized_path = Path(str(manifest.get("normalized_trace_path") or ""))
        if not normalized_path.is_absolute():
            normalized_path = (manifest_path.parent / normalized_path).resolve()
        raw_sha = str(manifest.get("raw_source_sha256") or "")
        normalized_sha = str(manifest.get("normalized_trace_sha256") or "")
        if not SHA256_RE.fullmatch(raw_sha):
            errors.append(f"{manifest_path}: raw_source_sha256 is not full SHA-256")
        if not SHA256_RE.fullmatch(normalized_sha):
            errors.append(f"{manifest_path}: normalized_trace_sha256 is not full SHA-256")
        elif not normalized_path.is_file():
            errors.append(f"{manifest_path}: normalized_trace_path missing: {normalized_path}")
        elif sha256_file(normalized_path) != normalized_sha:
            errors.append(f"{manifest_path}: normalized_trace_sha256 mismatch")
        coverage = manifest.get("coverage") or {}
        if coverage.get("sequence_contiguous") is not True:
            errors.append(f"{manifest_path}: coverage.sequence_contiguous is not true")
        last_sequence = 0
        if normalized_path.is_file():
            try:
                sequences = normalized_sequences(normalized_path)
            except (OSError, ValueError) as exc:
                errors.append(f"{manifest_path}: normalized trace sequence check failed: {exc}")
            else:
                last_sequence = len(sequences)
                if sequences != list(range(1, last_sequence + 1)):
                    errors.append(f"{manifest_path}: normalized trace sequence is not exactly 1..N")
                stated_events = coverage.get("normalized_events", coverage.get("event_count"))
                if isinstance(stated_events, int) and stated_events != last_sequence:
                    errors.append(
                        f"{manifest_path}: coverage event count {stated_events} != {last_sequence}"
                    )
                if isinstance(coverage.get("last_sequence"), int) and coverage["last_sequence"] != last_sequence:
                    errors.append(
                        f"{manifest_path}: coverage.last_sequence {coverage['last_sequence']} != {last_sequence}"
                    )
                try:
                    source_manifest = session_manifest(normalized_path)
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    errors.append(f"{manifest_path}: session manifest check failed: {exc}")
                else:
                    if (source_manifest.get("source") or {}).get("sha256") != raw_sha:
                        errors.append(f"{manifest_path}: raw_source_sha256 mismatch")
                    source_events = (source_manifest.get("coverage") or {}).get("normalized_events")
                    if source_events != last_sequence:
                        errors.append(
                            f"{manifest_path}: session coverage {source_events} != {last_sequence}"
                        )

        candidate_drafts = {candidate.get("draft_path") for candidate in manifest.get("candidates") or []}
        for candidate in manifest.get("candidates") or []:
            form = candidate.get("knowledge_form")
            candidate_forms[str(form)] += 1
            if form not in ROLE_SETS:
                errors.append(f"{manifest_path}: invalid knowledge_form {form!r}")
                continue
            roles = candidate.get("evidence_roles") or {}
            missing = ROLE_SETS[form] - set(roles)
            if missing:
                errors.append(f"{manifest_path}: {form} missing roles {sorted(missing)}")
            for role in ROLE_SETS[form]:
                if not roles.get(role):
                    errors.append(f"{manifest_path}: {form} role {role} is empty")
            candidate_anchors = list(candidate.get("evidence_anchors") or [])
            for role_anchors in roles.values():
                candidate_anchors.extend(role_anchors or [])
            artifacts = candidate.get("mechanism_artifacts") or []
            if not artifacts:
                errors.append(f"{manifest_path}: {form} has no mechanism_artifacts")
            for artifact in artifacts:
                if artifact.get("role") not in roles:
                    errors.append(f"{manifest_path}: artifact role {artifact.get('role')!r} is not an evidence role")
                if artifact.get("kind") not in ARTIFACT_KINDS:
                    errors.append(f"{manifest_path}: invalid artifact kind {artifact.get('kind')!r}")
                if artifact.get("reconstruction_method") not in RECONSTRUCTION_METHODS:
                    errors.append(f"{manifest_path}: invalid reconstruction_method {artifact.get('reconstruction_method')!r}")
                if artifact.get("verbatim_verified") is not True:
                    errors.append(f"{manifest_path}: artifact is not verbatim_verified")
                if not artifact.get("anchors"):
                    errors.append(f"{manifest_path}: artifact has no anchors")
                if not artifact.get("path") or not artifact.get("symbol_or_target"):
                    errors.append(f"{manifest_path}: artifact lacks path/symbol_or_target")
                candidate_anchors.extend(artifact.get("anchors") or [])
            for anchor in candidate_anchors:
                anchor_error = check_anchor(
                    anchor, trace_id, raw_sha, normalized_sha, last_sequence
                )
                if anchor_error:
                    errors.append(f"{manifest_path}: {anchor_error}")
            draft = candidate.get("draft_path")
            if not draft or not (manifest_path.parent / draft).is_file():
                errors.append(f"{manifest_path}: candidate draft missing: {draft}")
            else:
                draft_text = (manifest_path.parent / draft).read_text(encoding="utf-8")
                if FORM_SECTIONS[form] not in draft_text:
                    errors.append(f"{manifest_path}: candidate draft lacks {FORM_SECTIONS[form]}")

        candidate_decision_counts = Counter()
        for decision in manifest.get("rereview_decisions") or []:
            index = decision.get("queue_index")
            if not isinstance(index, int) or index not in expected:
                errors.append(f"{manifest_path}: invalid queue_index {index!r}")
                continue
            if index in decisions:
                errors.append(f"{manifest_path}: duplicate queue_index {index}")
            decisions[index] = decision
            if expected[index].get("trace_id") != trace_id:
                errors.append(f"{manifest_path}: queue_index {index} belongs to another trace")
            if decision.get("source_kind") != expected[index].get("source_kind"):
                errors.append(f"{manifest_path}: queue_index {index} source_kind mismatch")
            if decision.get("old_reason") != expected[index].get("reason"):
                errors.append(f"{manifest_path}: queue_index {index} old_reason mismatch")
            if decision.get("terminal") not in {"candidate", "skipped"}:
                errors.append(f"{manifest_path}: queue_index {index} lacks terminal state")
            if decision.get("terminal") == "candidate":
                candidate_draft = decision.get("candidate_draft")
                candidate_decision_counts[candidate_draft] += 1
                if candidate_draft not in candidate_drafts:
                    errors.append(
                        f"{manifest_path}: queue_index {index} candidate_draft is not a manifest candidate"
                    )
            if decision.get("terminal") == "skipped":
                if not decision.get("reason"):
                    errors.append(f"{manifest_path}: skipped queue_index {index} lacks reason")
                if decision.get("reclassification_checked") is not True:
                    errors.append(
                        f"{manifest_path}: skipped queue_index {index} lacks reclassification_checked"
                    )
        for candidate_draft in candidate_drafts:
            if candidate_decision_counts[candidate_draft] != 1:
                errors.append(
                    f"{manifest_path}: candidate {candidate_draft!r} maps to "
                    f"{candidate_decision_counts[candidate_draft]} queue decisions"
                )

    missing_indices = sorted(set(expected) - set(decisions))
    extra_indices = sorted(set(decisions) - set(expected))
    if missing_indices:
        errors.append(f"queue coverage missing {len(missing_indices)} indices; first={missing_indices[:10]}")
    if extra_indices:
        errors.append(f"queue coverage has {len(extra_indices)} extras; first={extra_indices[:10]}")

    summary = {
        "queue_items": len(expected),
        "decisions": len(decisions),
        "manifests": len(manifests),
        "candidate_forms": dict(sorted(candidate_forms.items())),
        "errors": len(errors),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
