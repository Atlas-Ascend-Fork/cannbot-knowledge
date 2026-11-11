---
type: Optimization
title: 'F9: eval_harness:msprof_case_loader:root_jsonl_poisoning'
description: 进化变体的 canonical `evaluation_results.json` 里 `timing_summary.n_cases_total` 变成 10（或 6/16 等），
tags:
- task.debugging
- topic.architecture
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/4917980395de8b8703aa7ec62213fafbe7bec01e/plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/runbooks/failure-patterns/f9-msprof-case-loader-jsonl-poisoning.md
  role: evidence
created_at: '2026-10-30T13:25:00Z'
updated_at: '2026-10-30T13:25:00Z'
platforms:
- a2
- a3
---

# F9: eval_harness:msprof_case_loader:root_jsonl_poisoning

> 进化失败模式元数据（迁移自旧 OKF，机器可读副本见 ascendc-evolution-knowledge/references/okf_compat.json）：
> key: "eval_harness:msprof_case_loader:root_jsonl_poisoning"
> phenomenon: precision_failure
> severity: blocking
> failed_combination: []
> operator_type: ["attention", "flash_attention", "matmul", "reduction", "elementwise"]
> occurrences: 1

## Symptom
进化变体的 canonical `evaluation_results.json` 里 `timing_summary.n_cases_total` 变成 10（或 6/16 等），
而官方 case 集是 50 例；随后 `wm_ops.py refine` 以 `case_subset_evaluation: n_cases_total=10 < full=50`
把该节点判为 failed 并拒绝生成子节点（lane 直接 `no_valid_child` 关闭）。现象隐蔽：编译/精度都通过，只有计时 case 数不对。

## Root cause class
评测链的 case 加载器（`ops-profiling` 的 `msprof_perf_summary._load_cases_jsonl`）优先 glob 算子目录**根目录**的
`*_perf_cases.jsonl`，其次**任意 `*.jsonl`**，再其次 `*.json`。子 agent 把 A/B 探针输出
（`ab_interleaved.jsonl`，每行是 `{op_dir, per_case_us, geomean_us}`）留在候选根目录时，加载器把它当成 case 集，
官方 50 例计时被静默替换（或被解析失败后按残缺集合计时）。

## Failed combination
- 子 agent 在候选根目录写 A/B/诊断 JSONL（`ab_*.jsonl`、`*_probe.jsonl`）；
- 与 `evaluate_ascendc.sh --mode=certify`（quick-batch 计时）叠加即触发。

## Resolution
1. 所有 A/B/诊断产物写到子目录（如 `<candidate>/ab/`）或使用非 `.jsonl` 扩展名（`.jsonl.txt`）。
2. 评估前自检：`ls <candidate>/*.jsonl` 必须为空；`timing_summary.n_cases_total` 必须 == 官方 case 文件行数。
3. 若已污染：把 jsonl 移出根目录后重跑 certify；world-model 侧用新 worker-key 重新 refine 修复节点记录
   （旧记录会留下 `case_subset_evaluation` 的 failure_reason，需要手动清）。

## Evidence
105_FusedInferAttentionScoreTorch_evo_20261030_094853 round_1/parallel_0：子 agent 把 6 行 A/B JSONL 留在根目录，
certify 只测 10 例计时，refine 判 `n1` failed（case_subset_evaluation）。同期 round_1/parallel_2 的子 agent
自行发现同一问题（"msprof 的 case 加载器会 glob 候选根目录 *.jsonl"）并主动把产物移到 `perf_tuning/`。
