---
{
  "type": "Runbook",
  "title": "mock CPU 引擎跨机 digest 的机器字段剥离与快速筛查边界",
  "description": "来源后续修订把剥离路径改为相对 load_payload，并对未命中的规则报错。fixture 观察到规范化哈希一致，但截断 MD5 相等只是快速筛查，不能证明 payload 逐字段相同或性能可比。",
  "tags": [
    "task.implementation",
    "topic.data_pipeline"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# mock CPU 引擎跨机 digest 的机器字段剥离与快速筛查边界

## 适用场景

openOneRec mock CPU 引擎的负载摘要包含绝对路径、mtime 或 CPU 数量，跨机对照需要区分机器标识变化与负载语义变化。mock 实验没有验证真实模型的设备计算或推荐质量。

## 触发与观测

来源三台机器的 CPU 数分别为 192/384/96，路径与 mtime 也有机器差异。原始截断 digest 为 6960c4fb；剥离后 fixture 报 b84ff48c，并报告六类规则有命中。单个 fixture 只覆盖该 fixture，不能证明字段列表对未来 schema 始终充分。

## 探针与操作

先核对 digest 的输入根是否已取出 `load_payload`。初版仍写 `("load_payload", "tokenizer_path")`，无法在此根下命中；后续改为 `("tokenizer_path",)`，并增加 unmatched 规则检查。所有规则都命中后再比较规范化 payload；若需要证明字段一致，应无条件比较原始叶值，而不是仅在哈希不同时才比较。

## 机制与判别

以下完整机制由来源后续三次 Edit 应用到初版重建，保留了实际比较器的局限：它仍可能在截断哈希相等时跳过逐叶比较。

```
#!/usr/bin/env python3
"""Cross-machine determinism check for openOneRec mock-engine run identity.

The run digest written by `mock_config_digest` covers the whole load payload,
which deliberately includes machine-local identity: absolute paths, file
mtimes and `os.cpu_count()`. Two hosts therefore can never share a raw digest
even when the code, the data content and every knob are identical. This tool
recomputes the digest over the machine-independent remainder so cross-host
runs become comparable, and reports exactly which leaves were dropped.

Usage:
  normalized_digest.py PROVENANCE.json [PROVENANCE.json ...]
  normalized_digest.py --compare BASE.json OTHER.json

With two or more inputs (or --compare) the normalized payloads are also
diffed leaf by leaf, which is the three-way code/data/parameter diff needed
when a gate fails.
"""

import argparse
import copy
import hashlib
import json
import os
import sys

# Leaves that carry machine-local identity rather than run semantics. Paths
# are relative to `load_payload`, which is what mock_config_digest hashes.
# `*` matches every key of a mapping.
STRIPPED_LEAVES = (
    (("tokenizer_path",), "absolute tokenizer path"),
    (("engine_mock_config", "tokenizer_fingerprint", "path"), "absolute tokenizer path"),
    (("engine_mock_config", "data_identity", "data_dir"), "absolute data dir"),
    (("engine_mock_config", "data_identity", "files", "*", "path"), "absolute parquet path"),
    (("engine_mock_config", "data_identity", "files", "*", "mtime"), "filesystem mtime"),
    (("engine_mock_config", "cluster_budget", "total_cpu_budget"), "os.cpu_count()"),
)


def _digest(payload):
    """Mirror mock_config_digest: same serialization, same truncation."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()[:8]


def _strip(node, segments, dropped, trail=()):
    """Remove one STRIPPED_LEAVES entry in place, recording what was removed."""
    if not segments:
        return
    head, rest = segments[0], segments[1:]
    if not isinstance(node, dict):
        return
    if head == "*":
        for key in list(node):
            _strip(node[key], rest, dropped, trail + (key,))
        return
    if head not in node:
        return
    if rest:
        _strip(node[head], rest, dropped, trail + (head,))
    else:
        dropped["/".join(trail + (head,))] = node.pop(head)


def normalize(provenance):
    """Return (normalized_payload, normalized_digest, dropped, unmatched).

    `unmatched` lists strip patterns that removed nothing. A pattern that
    silently stops matching is how machine-local identity leaks back into the
    normalized digest, so callers must treat it as a hard error.
    """
    payload = copy.deepcopy(provenance["load_payload"])
    dropped = {}
    unmatched = []
    for segments, reason in STRIPPED_LEAVES:
        before = len(dropped)
        _strip(payload, segments, dropped)
        if len(dropped) == before:
            unmatched.append(("/".join(segments), reason))
    return payload, _digest(payload), dropped, unmatched


def flatten(node, trail=()):
    """Flatten a payload into {'/'.join(path): scalar} for leaf diffing."""
    flat = {}
    if isinstance(node, dict):
        for key, value in node.items():
            flat.update(flatten(value, trail + (str(key),)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            flat.update(flatten(value, trail + (str(index),)))
    else:
        flat["/".join(trail)] = node
    return flat


def raw_digest_dir(path):
    """The raw digest is the name of the mock/<digest>/ directory holding it."""
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return parent if len(parent) == 8 else "?"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("provenance", nargs="+", help="mock_provenance.json path(s)")
    parser.add_argument("--compare", action="store_true",
                        help="force a leaf-level diff of the normalized payloads")
    parser.add_argument("--json", action="store_true",
                        help="also dump the normalized payload as JSON")
    args = parser.parse_args()

    results = []
    strip_ok = True
    for path in args.provenance:
        with open(path, "r", encoding="utf-8") as handle:
            provenance = json.load(handle)
        payload, digest, dropped, unmatched = normalize(provenance)
        results.append((path, payload, digest, dropped, provenance))
        print(f"=== {path}")
        print(f"  raw digest dir : {raw_digest_dir(path)}")
        print(f"  normalized     : {digest}")
        print(f"  code_version   : {provenance.get('code_version')}")
        print(f"  dropped leaves : {len(dropped)}")
        for name, value in sorted(dropped.items()):
            print(f"    - {name} = {value!r}")
        for name, reason in unmatched:
            strip_ok = False
            print(f"  WARNING strip pattern matched nothing: {name} ({reason})")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))

    if not strip_ok:
        print("\n=== ABORT: a strip pattern did not match; the normalized "
              "digest is not trustworthy")
        return 2

    if args.compare or len(results) > 1:
        base_path, base_payload, base_digest, _, _ = results[0]
        base_flat = flatten(base_payload)
        all_equal = True
        for path, payload, digest, _, _ in results[1:]:
            print(f"\n=== normalized diff: {os.path.basename(base_path)} vs {path}")
            if digest == base_digest:
                print("  MATCH: normalized digests are identical")
                continue
            all_equal = False
            other = flatten(payload)
            for key in sorted(set(base_flat) | set(other)):
                left, right = base_flat.get(key, "<absent>"), other.get(key, "<absent>")
                if left != right:
                    print(f"  DIFF {key}\n    base : {left!r}\n    other: {right!r}")
        print(f"\n=== all normalized digests equal: {all_equal}")
        return 0 if all_equal else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

## 验证信号

来源后续输出报告被剥离字段已命中、fixture 规范化哈希相同，原样 payload 重算与原摘要相同。这些是特定样本的一致性检查，不证明无哈希碰撞、所有字段全等或不同机器性能等效。代码在规则无命中时返回 2，不把缺失 schema 静默当作通过。

## 适用与失效边界

剥离规则必须由负载语义审查决定，不能为了使哈希相同而任意删字段；CPU budget、数据位置等字段也可能影响性能，规范化后仍须分别控制。该工具不构成模型质量或跨机性能门禁。
