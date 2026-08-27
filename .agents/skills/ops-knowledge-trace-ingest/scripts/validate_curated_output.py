#!/usr/bin/env python3
"""Validate typed curator coverage and evidence audits."""

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
STATUSES = {"published", "deferred", "rejected", "covered", "merged"}
OPERATIONS = {"new", "upvote", "merge", "covered", "reject", "defer", "downvote"}
OPERATION_STATUS = {
    "new": "published",
    "upvote": "merged",
    "merge": "merged",
    "covered": "covered",
    "reject": "rejected",
    "defer": "deferred",
    "downvote": "merged",
}
ARTIFACT_KINDS = {"code", "config", "command", "output", "probe"}
RECONSTRUCTION_METHODS = {
    "full_snapshot",
    "base_plus_complete_edit_chain",
    "self_contained_event",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
ANCHOR_RE = re.compile(r"^([0-9a-f]{12})#([1-9][0-9]*)$")


def as_list(value):
    if isinstance(value, list):
        return value
    return [] if value in (None, "") else [value]


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def trace_length(path):
    sequences = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            event = json.loads(line)
            sequence = event.get("sequence", event.get("seq"))
            if not isinstance(sequence, int):
                raise ValueError(f"{path}:{line_number} lacks integer sequence")
            sequences.append(sequence)
    if sequences != list(range(1, len(sequences) + 1)):
        raise ValueError(f"{path}: sequence is not exactly 1..N")
    return len(sequences)


def validate_anchor(anchor, sources):
    match = ANCHOR_RE.fullmatch(str(anchor))
    if not match:
        return f"invalid anchor syntax {anchor!r}"
    prefix, sequence_text = match.groups()
    matches = [
        source for source in sources
        if source["raw_sha"].startswith(prefix) or source["normalized_sha"].startswith(prefix)
    ]
    if not matches:
        return f"anchor {anchor!r} does not identify a recorded source"
    sequence = int(sequence_text)
    if all(sequence > source["last_sequence"] for source in matches):
        return f"anchor {anchor!r} exceeds its source sequence range"
    return None


def validate_reconstruction(entry, snapshot, sources, errors):
    """Require every accepted trace draft to carry its own coverage receipt."""
    label = entry.get("target_slug") or entry.get("draft") or "<entry>"
    registered_paths = {
        str(Path(str(path)).resolve())
        for path in as_list(snapshot.get("normalized_trace_path"))
    }
    for draft_text in as_list(entry.get("source_drafts")):
        draft = Path(str(draft_text))
        reconstruction_path = draft.parent / "reconstruction.json"
        try:
            reconstruction = json.loads(
                reconstruction_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: invalid reconstruction {reconstruction_path}: {exc}")
            continue
        trace_id = draft.parent.name
        if reconstruction.get("trace_id") != trace_id:
            errors.append(f"{label}: reconstruction trace_id mismatch for {trace_id}")
        normalized_path = Path(
            str(reconstruction.get("normalized_trace_path") or "")
        )
        if not normalized_path.is_absolute():
            normalized_path = (reconstruction_path.parent / normalized_path).resolve()
        else:
            normalized_path = normalized_path.resolve()
        if str(normalized_path) not in registered_paths:
            errors.append(
                f"{label}: reconstruction source is not registered for {trace_id}"
            )
            continue
        matching_source = next(
            (
                source for source in sources
                if source.get("path") == str(normalized_path)
            ),
            None,
        )
        if matching_source is None:
            errors.append(f"{label}: reconstruction source unavailable for {trace_id}")
            continue
        if reconstruction.get("raw_source_sha256") != matching_source["raw_sha"]:
            errors.append(f"{label}: reconstruction raw SHA mismatch for {trace_id}")
        if reconstruction.get("normalized_trace_sha256") != matching_source["normalized_sha"]:
            errors.append(
                f"{label}: reconstruction normalized SHA mismatch for {trace_id}"
            )
        coverage = reconstruction.get("coverage") or {}
        expected_count = matching_source["last_sequence"]
        expected = {
            "first_sequence": 1,
            "last_sequence": expected_count,
            "sequence_count": expected_count,
            "sequence_contiguous": True,
            "normalized_events": expected_count,
        }
        for key, value in expected.items():
            if coverage.get(key) != value:
                errors.append(
                    f"{label}: reconstruction coverage {key} mismatch for {trace_id}"
                )


def validate_trace_snapshot(entry, snapshot, errors):
    label = entry.get("target_slug") or entry.get("draft") or "<entry>"
    paths = as_list(snapshot.get("normalized_trace_path"))
    raw_shas = as_list(snapshot.get("raw_source_sha256"))
    normalized_shas = as_list(snapshot.get("normalized_trace_sha256"))
    if not paths or not all(Path(str(path)).is_file() for path in paths):
        errors.append(f"{label}: trace_snapshot normalized paths missing")
    if not raw_shas or not all(SHA256_RE.fullmatch(str(value)) for value in raw_shas):
        errors.append(f"{label}: trace_snapshot raw SHA-256 invalid")
    if not normalized_shas or not all(
        SHA256_RE.fullmatch(str(value)) for value in normalized_shas
    ):
        errors.append(f"{label}: trace_snapshot normalized SHA-256 invalid")
    sources = []
    if not (len(paths) == len(raw_shas) == len(normalized_shas)):
        errors.append(f"{label}: trace_snapshot path/SHA arrays do not align")
    else:
        for path_text, raw_sha, normalized_sha in zip(paths, raw_shas, normalized_shas):
            path = Path(str(path_text))
            if path.is_file() and sha256_file(path) != normalized_sha:
                errors.append(f"{label}: normalized trace SHA-256 mismatch for {path}")
                continue
            if not path.is_file():
                continue
            try:
                last_sequence = trace_length(path)
                source_manifest = json.loads(
                    (path.parent / "session_manifest.json").read_text(encoding="utf-8")
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{label}: source coverage check failed for {path}: {exc}")
                continue
            if (source_manifest.get("source") or {}).get("sha256") != raw_sha:
                errors.append(f"{label}: raw source SHA-256 mismatch for {path}")
            if (source_manifest.get("coverage") or {}).get("normalized_events") != last_sequence:
                errors.append(f"{label}: session coverage mismatch for {path}")
            sources.append(
                {
                    "path": str(path.resolve()),
                    "raw_sha": str(raw_sha),
                    "normalized_sha": str(normalized_sha),
                    "last_sequence": last_sequence,
                }
            )
    if snapshot.get("coverage_verified") is not True:
        errors.append(f"{label}: trace_snapshot coverage is not verified")
    validate_reconstruction(entry, snapshot, sources, errors)
    form = entry.get("knowledge_form")
    roles = snapshot.get("evidence_roles") or {}
    if form not in ROLE_SETS:
        errors.append(f"{label}: invalid knowledge_form {form!r}")
    else:
        missing = ROLE_SETS[form] - set(roles)
        if missing or any(not roles.get(role) for role in ROLE_SETS[form]):
            errors.append(f"{label}: trace_snapshot evidence roles incomplete")
    artifacts = snapshot.get("mechanism_artifacts") or []
    if not artifacts:
        errors.append(f"{label}: trace_snapshot mechanism_artifacts missing")
    for artifact in artifacts:
        required = (
            "role",
            "kind",
            "path",
            "symbol_or_target",
            "reconstruction_method",
        )
        if any(not artifact.get(key) for key in required):
            errors.append(f"{label}: incomplete mechanism artifact")
        if artifact.get("kind") not in ARTIFACT_KINDS:
            errors.append(f"{label}: invalid mechanism artifact kind")
        if artifact.get("reconstruction_method") not in RECONSTRUCTION_METHODS:
            errors.append(f"{label}: invalid reconstruction method")
        if artifact.get("role") not in roles:
            errors.append(f"{label}: mechanism artifact role is not an evidence role")
        if not artifact.get("anchors"):
            errors.append(f"{label}: mechanism artifact anchors missing")
        if artifact.get("verbatim_verified") is not True:
            errors.append(f"{label}: mechanism artifact is not verbatim verified")
    anchors = []
    for role_anchors in roles.values():
        anchors.extend(as_list(role_anchors))
    for artifact in artifacts:
        anchors.extend(as_list(artifact.get("anchors")))
    for anchor in anchors:
        anchor_error = validate_anchor(anchor, sources)
        if anchor_error:
            errors.append(f"{label}: {anchor_error}")


def validate_fixed_source(entry, source, errors):
    label = entry.get("target_slug") or entry.get("draft") or "<entry>"
    form = entry.get("knowledge_form")
    roles = source.get("evidence_roles") or {}
    if form not in ROLE_SETS or ROLE_SETS[form] - set(roles):
        errors.append(f"{label}: fixed_source evidence roles incomplete")
    revisions = as_list(source.get("revisions"))
    if not revisions or not all(REVISION_RE.fullmatch(str(value)) for value in revisions):
        errors.append(f"{label}: fixed_source revisions invalid")
    if form == "repair_recipe":
        for key in ("base_revision", "fixed_revision"):
            if not REVISION_RE.fullmatch(str(source.get(key) or "")):
                errors.append(f"{label}: fixed_source {key} invalid for repair_recipe")
    files = source.get("files") or []
    if not files:
        errors.append(f"{label}: fixed_source files missing")
    for item in files:
        required = (
            "role", "revision", "path", "symbol_or_target", "line_span", "blob_url"
        )
        if any(not item.get(key) for key in required):
            errors.append(f"{label}: incomplete fixed_source file evidence")
        if not REVISION_RE.fullmatch(str(item.get("revision") or "")):
            errors.append(f"{label}: fixed_source file revision invalid")
        if item.get("revision") not in revisions:
            errors.append(f"{label}: fixed_source file revision is not registered")
        if item.get("role") not in roles:
            errors.append(f"{label}: fixed_source file role is not an evidence role")
        if item.get("navigation_verified") is not True:
            errors.append(f"{label}: fixed_source navigation is not verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clusters", type=Path)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    clusters = json.loads(args.clusters.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    expected = {
        str(Path(member["draft"]))
        for cluster in clusters.get("clusters") or []
        for member in cluster.get("members") or []
    }
    expected.update(
        str(Path(member["draft"])) for member in clusters.get("unclustered") or []
    )
    entries = ledger.get("entries") or []
    covered = []
    errors = []
    status_counts = Counter()
    operation_counts = Counter()
    form_counts = Counter()
    for entry in entries:
        drafts = as_list(entry.get("source_drafts"))
        if not drafts:
            errors.append(f"entry {entry.get('cluster')!r} lacks source_drafts")
        covered.extend(str(Path(str(draft))) for draft in drafts)
        status = entry.get("status")
        status_counts[str(status)] += 1
        if status not in STATUSES:
            errors.append(f"entry {entry.get('cluster')!r} has invalid status {status!r}")
        operation = entry.get("operation")
        operation_counts[str(operation)] += 1
        if operation not in OPERATIONS:
            errors.append(
                f"entry {entry.get('cluster')!r} has invalid operation {operation!r}"
            )
        elif OPERATION_STATUS[operation] != status:
            errors.append(
                f"entry {entry.get('cluster')!r} operation/status mismatch: "
                f"{operation}/{status}"
            )
        if not entry.get("reason"):
            errors.append(f"entry {entry.get('cluster')!r} lacks reason")
        if status in {"published", "merged"} and not entry.get("target_slug"):
            errors.append(f"entry {entry.get('cluster')!r} lacks target_slug")
        form = entry.get("knowledge_form")
        form_counts[str(form)] += 1
        if form not in ROLE_SETS:
            errors.append(f"entry {entry.get('cluster')!r} has invalid form {form!r}")
        if status not in {"published", "merged"}:
            continue
        audit = entry.get("evidence_audit") or {}
        if audit.get("result") != "pass":
            errors.append(f"entry {entry.get('cluster')!r} evidence audit did not pass")
        mode = audit.get("mode")
        if mode == "trace_snapshot":
            if "fixed_source" in audit:
                errors.append(f"entry {entry.get('cluster')!r} mixes evidence modes")
            validate_trace_snapshot(entry, audit.get("trace_snapshot") or {}, errors)
        elif mode == "fixed_source":
            if "trace_snapshot" in audit:
                errors.append(f"entry {entry.get('cluster')!r} mixes evidence modes")
            validate_fixed_source(entry, audit.get("fixed_source") or {}, errors)
        else:
            errors.append(f"entry {entry.get('cluster')!r} has invalid evidence mode {mode!r}")

    counts = Counter(covered)
    missing = sorted(expected - set(covered))
    unknown = sorted(set(covered) - expected)
    duplicates = sorted(draft for draft, count in counts.items() if count != 1)
    if missing:
        errors.append(f"candidate coverage missing {len(missing)} drafts; first={missing[:5]}")
    if unknown:
        errors.append(f"candidate coverage has {len(unknown)} unknown drafts; first={unknown[:5]}")
    if duplicates:
        errors.append(f"candidate coverage duplicates {len(duplicates)} drafts; first={duplicates[:5]}")
    summary = {
        "candidates": len(expected),
        "covered_candidates": len(covered),
        "entries": len(entries),
        "statuses": dict(sorted(status_counts.items())),
        "operations": dict(sorted(operation_counts.items())),
        "forms": dict(sorted(form_counts.items())),
        "errors": len(errors),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
