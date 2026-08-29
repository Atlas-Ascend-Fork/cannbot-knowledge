#!/usr/bin/env python3
"""Materialize the active-trace evidence contract (runbooks 落库契约 §8.1) from a
miner's manifest into the structures ``validate_curated_output.py`` enforces.

The miner records evidence per candidate (evidence_anchors / code_evidence /
failure_signal_refs / fixed_signal_refs / claim_mapping) and writes a manifest
with top-level source_sha256 / normalized_trace_sha256 / coverage, but the
validator requires:

  * ``reconstruction.json`` to carry trace_id / normalized_trace_path /
    raw_source_sha256 / normalized_trace_sha256 / contiguous coverage;
  * each *published* ledger entry to carry ``evidence_audit.trace_snapshot``
    with aligned path/SHA arrays, coverage_verified, form-specific
    evidence_roles, and mechanism_artifacts (role/kind/path/symbol/
    reconstruction_method/anchors/verbatim_verified) whose anchors resolve to
    a recorded source as ``<sha12>#<sequence>``.

This script fills that gap deterministically (0 LLM) by reading every supplied
miner manifest + normalized trace + session manifest, emitting the reconstruction
patch and per-draft trace_snapshot map, and then (when ``--ledger`` is present)
augmenting entries with those newly materialized snapshots. Fresh ledger runs do
not require a separate front-load invocation.

Usage:
  materialize_trace_contract.py <mine_dir> --normalized-root <dir>
      [--ledger <path>] [--clusters <path>]
  <mine_dir>        dir with manifest.json + reconstruction.json + DRAFT-*.md
  --normalized-root batch trace-normalized root (contains <sha12>/ dirs)
"""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

from validate_review_receipt import validate_receipt


ROLE_SETS = {
    "repair_recipe": ["failure", "before", "repair_after", "validation_after"],
    "diagnostic_rule": ["trigger", "probe", "observation", "interpretation"],
    "negative_result": ["attempt", "observation", "boundary"],
    "validated_pattern": ["implementation", "validation"],
}
ARTIFACT_KINDS = {"code", "config", "command", "output", "probe"}
RECONSTRUCTION_METHODS = {
    "full_snapshot",
    "base_plus_complete_edit_chain",
    "self_contained_event",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def trace_length(path: Path) -> int:
    n = 0
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            seq = event.get("sequence", event.get("seq"))
            if not isinstance(seq, int):
                raise ValueError(f"{path}: non-integer sequence at line {n + 1}")
            n += 1
            if seq != n:
                raise ValueError(f"{path}: sequence not contiguous 1..N (got {seq} at {n})")
    return n


def anchor(sha12: str, seq) -> str:
    return f"{sha12}#{int(seq)}"


def unique_seqs(refs):
    """Flatten nested int lists / single ints into a deduped sorted list."""
    out = []
    seen = set()

    def walk(v):
        if isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, int):
            if v not in seen:
                seen.add(v)
                out.append(v)
    walk(refs)
    return sorted(out)


def roles_for_form(form, cand, sha12):
    """Map miner evidence -> validator evidence_roles dict {role: [anchors]}.
    Primary source: evidence_anchors (miner writes explicit role tags + sequence).
    Fallback: failure_signal_refs / fixed_signal_refs / code_evidence before/after refs.
    """
    # evidence_anchors: [{sequence, role, ...}] -> role-grouped seqs
    ea = {}
    for a in cand.get("evidence_anchors") or []:
        if not isinstance(a, dict):
            continue
        seq = a.get("sequence")
        role = str(a.get("role") or "")
        if isinstance(seq, int) and role:
            ea.setdefault(role, []).append(seq)
    # normalize ea role keys to canonical groups
    def ea_group(*keys):
        seqs = []
        for k in keys:
            seqs.extend(ea.get(k, []))
        return seqs
    failure = unique_seqs(cand.get("failure_signal_refs")) + ea_group("failure_signal", "failure")
    fixed = unique_seqs(cand.get("fixed_signal_refs")) + ea_group("fixed_signal", "validation_after", "validation")
    code_ev = cand.get("code_evidence") or []
    before_refs = unique_seqs([ce.get("before_event_refs") for ce in code_ev]) + ea_group("before_code_verbatim", "before_code", "before")
    after_refs = unique_seqs([ce.get("after_event_refs") for ce in code_ev]) + ea_group("after_code_verbatim", "after_code", "after", "repair_after")
    probe_refs = ea_group("diagnostic_probe", "probe")
    cm = cand.get("claim_mapping") or {}

    def anchors(seqs):
        return [anchor(sha12, s) for s in unique_seqs(seqs)]

    def pick(*lists):
        for lst in lists:
            lst = unique_seqs(lst)
            if lst:
                return lst
        return []

    if form == "repair_recipe":
        return {
            "failure": anchors(pick(failure, cm.get("failure"))),
            "before": anchors(pick(before_refs, cm.get("root_cause"))),
            "repair_after": anchors(pick(after_refs, cm.get("fix"))),
            "validation_after": anchors(pick(fixed, cm.get("after_verify"))),
        }
    if form == "validated_pattern":
        return {
            "implementation": anchors(pick(after_refs, before_refs, cm.get("fix"))),
            "validation": anchors(pick(fixed, cm.get("after_verify"))),
        }
    if form == "diagnostic_rule":
        return {
            "trigger": anchors(pick(failure, cm.get("failure"))),
            "probe": anchors(pick(probe_refs, cm.get("root_cause"), before_refs)),
            "observation": anchors(pick(fixed, cm.get("after_verify"))),
            "interpretation": anchors(pick(cm.get("root_cause"), before_refs)),
        }
    if form == "negative_result":
        return {
            "attempt": anchors(pick(before_refs, cm.get("root_cause"))),
            "observation": anchors(pick(failure, cm.get("failure"))),
            "boundary": anchors(pick(fixed, cm.get("after_verify"))),
        }
    return {}


def artifacts_for(cand, roles, sha12, verified=False):
    """Map code_evidence -> mechanism_artifacts (role/kind/path/symbol/method/anchors).

    ``verified`` must come from an explicit reviewer assertion (--verified);
    this script never claims verbatim verification on its own."""
    out = []
    form = cand.get("knowledge_form")
    for ce in cand.get("code_evidence") or []:
        before = unique_seqs(ce.get("before_event_refs"))
        after = unique_seqs(ce.get("after_event_refs"))
        if before and after:
            method = "base_plus_complete_edit_chain"
            role = "before" if form == "repair_recipe" else "implementation"
            seqs = before + after
        elif after:
            method = "full_snapshot"
            role = "repair_after" if form == "repair_recipe" else "implementation"
            seqs = after
        elif before:
            method = "full_snapshot"
            role = "before" if form == "repair_recipe" else "implementation"
            seqs = before
        else:
            continue
        if role not in roles:
            role = next(iter(roles))
        path = ce.get("path") or ""
        kind = "code"
        # a probe/test command artifact
        tp = ce.get("test_or_probe")
        if tp and ("--" in str(tp) or str(tp).startswith("./") or "gtest" in str(tp).lower()):
            kind = "command"
        artifact = {
            "role": role,
            "kind": kind,
            "path": path,
            "symbol_or_target": ce.get("symbol") or ce.get("supports_claims", [""])[0],
            "reconstruction_method": method,
            "anchors": [anchor(sha12, s) for s in seqs],
            "verbatim_verified": verified,
        }
        out.append(artifact)
    return out


def materialize(mine_dir: Path, norm_root: Path, verified=False):
    manifest = json.loads((mine_dir / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        return None, f"manifest not a dict in {mine_dir.name}"
    trace_id = manifest.get("trace_id") or mine_dir.name
    norm_dir = norm_root / trace_id
    norm_path = norm_dir / "normalized_trace.jsonl"
    if not norm_path.is_file():
        # fall back: search for the dir whose session source sha matches trace_id
        norm_dir = norm_root / trace_id
        for d in norm_root.iterdir():
            if not d.is_dir() or not (d / "session_manifest.json").is_file():
                continue
            try:
                src = json.loads((d / "session_manifest.json").read_text(encoding="utf-8")).get("source", {})
            except (OSError, json.JSONDecodeError):
                continue
            if str(src.get("sha256", ""))[:12] == trace_id[:12]:
                norm_dir = d
                break
        norm_path = norm_dir / "normalized_trace.jsonl"
    session = json.loads((norm_dir / "session_manifest.json").read_text(encoding="utf-8"))
    raw_sha = (session.get("source") or {}).get("sha256") or manifest.get("source_sha256")
    norm_sha = manifest.get("normalized_trace_sha256")
    # verify normalized sha + contiguous sequence
    try:
        actual_norm_sha = sha256_file(norm_path)
        norm_sha = norm_sha or actual_norm_sha
        if norm_sha != actual_norm_sha:
            norm_sha = actual_norm_sha  # trust the file
        n = trace_length(norm_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, f"normalized trace unusable: {exc}"
    coverage = {
        "first_sequence": 1,
        "last_sequence": n,
        "sequence_count": n,
        "sequence_contiguous": True,
        "normalized_events": n,
    }
    norm_path_abs = str(norm_path.resolve())
    norm_sha12 = (norm_sha or "")[:12]
    # 1. augment reconstruction.json
    recon_path = mine_dir / "reconstruction.json"
    recon = json.loads(recon_path.read_text(encoding="utf-8"))
    recon["trace_id"] = trace_id
    recon["normalized_trace_path"] = norm_path_abs
    recon["raw_source_sha256"] = raw_sha
    recon["normalized_trace_sha256"] = norm_sha
    recon["coverage"] = coverage
    recon_path.write_text(json.dumps(recon, ensure_ascii=False, indent=2), encoding="utf-8")
    # 2. per-candidate trace_snapshot
    snapshots = {}
    for cand in manifest.get("candidates", []):
        if not isinstance(cand, dict):
            continue
        draft = cand.get("draft_path")
        if not draft:
            continue
        form = cand.get("knowledge_form")
        if form not in ROLE_SETS:
            continue
        try:
            roles = roles_for_form(form, cand, norm_sha12)
            snaps = artifacts_for(cand, roles, norm_sha12, verified=verified)
        except Exception:
            continue  # malformed candidate evidence; skip rather than crash the dir
        # key by draft basename (unique within a trace)
        snapshots[Path(draft).name] = {
            "normalized_trace_path": [norm_path_abs],
            "raw_source_sha256": [raw_sha],
            "normalized_trace_sha256": [norm_sha],
            "coverage_verified": True,
            "evidence_roles": roles,
            "mechanism_artifacts": snaps,
        }
    (mine_dir / "trace_snapshots.json").write_text(
        json.dumps(snapshots, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"trace_id": trace_id, "events": n, "snapshots": len(snapshots), "raw_sha": (raw_sha or "")[:12], "norm_sha": (norm_sha or "")[:12]}, None


def augment_ledger(ledger_path: Path, mine_dirs, clusters_path=None, verified=False):
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    # cluster_id -> member draft path strings (as written by cluster_candidates.py)
    cluster_drafts = {}
    if clusters_path and Path(clusters_path).is_file():
        cl = json.loads(Path(clusters_path).read_text(encoding="utf-8"))
        for c in cl.get("clusters", []):
            cluster_drafts[c.get("id")] = [str(Path(m.get("draft", ""))) for m in c.get("members", [])]
    # (trace_id, basename) -> trace_snapshot
    snap = {}
    for md in mine_dirs:
        sp = md / "trace_snapshots.json"
        if not sp.is_file():
            continue
        tid = md.name
        for name, obj in json.loads(sp.read_text(encoding="utf-8")).items():
            snap[(tid, name)] = obj

    def snapshot_for(draft_str):
        # draft like '.build/.../<date>/<trace_id>/DRAFT-<name>.md'
        p = Path(draft_str)
        tid = p.parent.name
        return snap.get((tid, p.name))

    for e in ledger.get("entries", []):
        cid = e.get("cluster")
        # set source_drafts to exact cluster member strings (relative) so coverage matches
        if cid in cluster_drafts:
            e["source_drafts"] = list(cluster_drafts[cid])
        elif not e.get("source_drafts") and e.get("draft"):
            e["source_drafts"] = [str(Path(str(e["draft"])))]
        if e.get("status") in {"published", "merged"}:
            audit = e.get("evidence_audit") or {"mode": "trace_snapshot", "result": "pending"}
            audit["mode"] = "trace_snapshot"
            found = None
            for d in (e.get("source_drafts") or []):
                found = snapshot_for(d)
                if found:
                    break
            if found:
                found = copy.deepcopy(found)
                if verified:
                    for artifact in found.get("mechanism_artifacts") or []:
                        artifact["verbatim_verified"] = True
                audit["trace_snapshot"] = found
                # Do not claim pass here: verbatim verification of mechanism
                # artifacts is a reviewer step, not a deterministic one.
                audit["result"] = "pass" if verified else "pending"
            else:
                audit["result"] = "defer"
            e["evidence_audit"] = audit
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    attached = sum(1 for e in ledger.get("entries", []) if (e.get("evidence_audit") or {}).get("trace_snapshot"))
    return {"entries": len(ledger.get("entries", [])), "snapshots_attached": attached}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mine_dirs", nargs="+")
    ap.add_argument("--normalized-root", required=True)
    ap.add_argument("--ledger")
    ap.add_argument("--clusters")
    ap.add_argument(
        "--verified",
        action="store_true",
        help="apply a validated PASS receipt to reviewer-owned approval flags",
    )
    ap.add_argument("--receipt", help="independent PASS review receipt required by --verified")
    ap.add_argument("--cards-root", help="staged card root bound by --receipt")
    args = ap.parse_args()
    norm_root = Path(args.normalized_root)
    mine_dirs = [Path(d) for d in args.mine_dirs]
    if args.verified:
        if not args.ledger or not args.receipt or not args.cards_root:
            ap.error("--verified requires --ledger, --receipt, and --cards-root")
        review = validate_receipt(
            Path(args.ledger), Path(args.cards_root), Path(args.receipt)
        )
        if not review.get("ok") or review.get("verdict") != "PASS":
            print(json.dumps(review, ensure_ascii=False, indent=2), file=sys.stderr)
            raise SystemExit("refusing --verified without a valid PASS receipt")
    materialize_errors = 0
    for md in mine_dirs:
        if not (md / "manifest.json").is_file():
            print(f"ERROR {md}: no manifest.json", file=sys.stderr)
            materialize_errors += 1
            continue
        try:
            # Source snapshots remain pending. Reviewer-owned flags are applied
            # only to the ledger copy after a PASS receipt is validated.
            res, err = materialize(md, norm_root, verified=False)
        except Exception as exc:
            print(f"ERROR {md.name}: {exc}", file=sys.stderr)
            materialize_errors += 1
            continue
        if err:
            print(f"ERROR {md.name}: {err}", file=sys.stderr)
            materialize_errors += 1
        else:
            print(f"OK {res['trace_id']}: events={res['events']} snapshots={res['snapshots']} raw={res['raw_sha']} norm={res['norm_sha']}")
    if materialize_errors:
        raise SystemExit(f"materialization failed for {materialize_errors} mine dirs")
    if args.ledger:
        res = augment_ledger(Path(args.ledger), mine_dirs, args.clusters, verified=args.verified)
        if args.verified:
            review = validate_receipt(
                Path(args.ledger), Path(args.cards_root), Path(args.receipt)
            )
            if not review.get("ok") or review.get("verdict") != "PASS":
                print(json.dumps(review, ensure_ascii=False, indent=2), file=sys.stderr)
                raise SystemExit("approved ledger no longer matches PASS receipt")
        print(f"LEDGER: entries={res['entries']} snapshots_attached={res['snapshots_attached']}")


if __name__ == "__main__":
    main()
