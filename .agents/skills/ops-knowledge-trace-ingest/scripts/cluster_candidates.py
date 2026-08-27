#!/usr/bin/env python3
"""草稿确定性预聚类（批量 curate 的 ④a 步骤）：0 LLM、纯 stdlib。

把多条 trace 的 miner 草稿按「同根因」特征聚成簇，供 curator 簇级门控与
跨 trace 复现判定使用。

用法：
    python3 cluster_candidates.py <草稿目录1> [<草稿目录2> ...] -o clusters.json

输入：每个草稿目录（.build/ops-knowledge-trace-ingest/<日期>/<trace_id>/，含
DRAFT-*.md + manifest.json）。簇特征取自 manifest 候选的内部 taxonomy
（type/area + knowledge_form + phenomenon + solution_layer + signal 共享词）+ 草稿正文
根因句字符 bigram。
输出：clusters.json
    {"clusters": [{"id": "c1", "members": [{"draft": "<路径>", "trace_id": "..."}],
      "trace_ids": [...], "type": "...", "knowledge_form": "...", "phenomenon": "...", "solution_layer": "...",
      "signals": [...], "root_cause": "<根因句>", "cross_trace": <int>}], "unclustered": [...]}

相似度 = 0.5*Jaccard(signal 词) + 0.5*Jaccard(根因 bigram)；阈值默认 0.35。
漏并后果轻（同 nugget 落两次 → 下次 upgrade 合并）；误并由 curator 判定时拆出。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT_CAUSE_RE = re.compile(r"## 根因\s*\n(.*?)(?=\n## |\Z)", re.DOTALL)
FORMS = {
    "repair_recipe",
    "diagnostic_rule",
    "negative_result",
    "validated_pattern",
}


def root_cause(text):
    m = ROOT_CAUSE_RE.search(text)
    if not m:
        return ""
    return " ".join(m.group(1).split())[:300]


def bigrams(s):
    s = re.sub(r"\W+", "", s.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def tokenize(signals):
    return set(re.findall(r"[a-z0-9_]{2,}", " ".join(signals).lower()))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def collect_candidates(dirs):
    out = []
    for d in dirs:
        d = Path(d)
        if not d.is_dir():
            print("skip (not a dir): %s" % d, file=sys.stderr)
            continue
        trace_id = d.name
        manifest_path = d / "manifest.json"
        if not manifest_path.is_file():
            print("skip (no manifest.json): %s" % d, file=sys.stderr)
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for cand in manifest.get("candidates") or []:
            draft = cand.get("draft_path")
            if not draft:
                continue
            p = d / draft
            if not p.is_file():
                print("skip (missing draft): %s" % p, file=sys.stderr)
                continue
            text = p.read_text(encoding="utf-8")
            knowledge_form = cand.get("knowledge_form")
            if knowledge_form not in FORMS:
                raise ValueError(f"{p}: missing or invalid knowledge_form {knowledge_form!r}")
            out.append({
                "draft": str(p),
                "trace_id": trace_id,
                "type": cand.get("type") or cand.get("area") or "",
                "knowledge_form": knowledge_form,
                "phenomenon": cand.get("phenomenon", ""),
                "solution_layer": cand.get("solution_layer", ""),
                "signals": cand.get("signal") or [],
                "root_cause": root_cause(text),
            })
    return out


def similarity(a, b):
    if a["knowledge_form"] != b["knowledge_form"]:
        return 0.0
    if a["phenomenon"] != b["phenomenon"] or a["solution_layer"] != b["solution_layer"]:
        base = 0.0
    else:
        base = 0.2
    s1, s2 = tokenize(a["signals"]), tokenize(b["signals"])
    r1, r2 = bigrams(a["root_cause"]), bigrams(b["root_cause"])
    return base + 0.4 * jaccard(s1, s2) + 0.4 * jaccard(r1, r2)


def cluster(cands, threshold):
    clusters = []
    for c in cands:
        best, best_sim = None, threshold
        for cl in clusters:
            rep = cl["members"][0]
            sim = similarity(c, rep)
            if sim > best_sim:
                best, best_sim = cl, sim
        if best is None:
            clusters.append({"members": [c]})
        else:
            best["members"].append(c)
    result = []
    for i, cl in enumerate(clusters, 1):
        reps = sorted(cl["members"], key=lambda m: (-len(m["signals"]), -len(m["root_cause"])))
        rep = reps[0]
        result.append({
            "id": "c%d" % i,
            "members": [{"draft": m["draft"], "trace_id": m["trace_id"]} for m in sorted(cl["members"], key=lambda m: m["trace_id"])],
            "trace_ids": sorted({m["trace_id"] for m in cl["members"]}),
            "cross_trace": len({m["trace_id"] for m in cl["members"]}),
            "type": rep["type"],
            "knowledge_form": rep["knowledge_form"],
            "phenomenon": rep["phenomenon"],
            "solution_layer": rep["solution_layer"],
            "signals": rep["signals"],
            "root_cause": rep["root_cause"],
            "member_count": len(cl["members"]),
        })
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+", help="one or more miner staging directories")
    ap.add_argument("-o", "--output", default="clusters.json")
    ap.add_argument("--threshold", type=float, default=0.35)
    args = ap.parse_args()
    cands = collect_candidates(args.dirs)
    if not cands:
        print("no DRAFT candidates found", file=sys.stderr)
        sys.exit(1)
    clusters = cluster(cands, args.threshold)
    payload = {"candidate_count": len(cands), "cluster_count": len(clusters),
               "cross_trace_clusters": sum(1 for c in clusters if c["cross_trace"] > 1),
               "threshold": args.threshold, "clusters": clusters}
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"candidate_count": len(cands), "cluster_count": len(clusters),
                      "cross_trace_clusters": sum(1 for c in clusters if c["cross_trace"] > 1),
                      "output": args.output}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
