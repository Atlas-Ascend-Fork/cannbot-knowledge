---
type: Optimization
title: ES1 向量排序 route 的 O(N) radix-select 直接选择
description: 对 ES1 向量排序 route 用 O(N) radix-select 直接选出 top-k，替代 O(N log N) 完整排序。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-o-n-radix-select-es1-vecsort.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "radix 桶宽选择必须匹配向量宽度与内存带宽",
      "尾桶处理、索引去重和 top-k 边界必须与 golden 语义一致"
    ],
    "excluded_conditions": [
      "n 小或 k 接近 n 时选择收益消失，应走原排序",
      "非整数/无自然按位序的 dtype 或分桶退化时不用 radix 路径"
    ],
    "required_conditions": [
      "n/k 比值足够大，使 O(N) 选择相对 O(N log N) 排序有净收益",
      "输入为向量排序 route，且 radix 分桶可用向量指令高效表达",
      "目标 case 通过运行 routing 落入 ES1 向量排序分支"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "b2b4c15032bda85a6c3d820b728e274d7330a4f2e053a4b95644b30b3b0ff495",
      "decision_sha256": "fd7eff06c33f62263d255c3b9fbd1d27946e719e2a1de2d817f8aad90ff1cd26",
      "operator_class": "sort-select",
      "performance_sha256": "5f2c9abab46a5d3ffec5837d4f540b49d38876b07e28a8cbee9f8df9d53253c6",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "a19777c6e3353fb3f069793a5b0b0ad5ca3bbe46ee9d4457692a721e092658b0",
      "verify_sha256": "aa4212b5a7709ddf7f997723af476ed89a8cd1463effd8c569b3a3992e7e2f3f"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "full-sort-overhead",
      "k-far-less-than-n"
    ],
    "dtypes": [
      "int32",
      "int64",
      "fp16",
      "fp32"
    ],
    "pattern": "radix-select",
    "structure": [
      "vector-sort-route",
      "bucket-recursion"
    ]
  },
  "gain": "case17 1.2349x、case8 1.1954x、case12 1.1197x；0 regression；官方 +0.104 pts",
  "generality": "op_class",
  "id": "TOPK-O-N-RADIX-SELECT-ES1",
  "implementation_steps": [
    "确认 target case 的 runtime route 落在 ES1 向量排序分支",
    "实现按关键位分桶的 radix-select，递归只进包含第 k 大的桶",
    "用向量指令批处理桶内比较，把 top-k 元素提取到输出",
    "对不适用 case 保留原排序回退，验证边界与去重",
    "单 case probe（probe_required）后全量 verify + measure 确认无回归"
  ],
  "intent": "消除 ES1 向量排序 case 中完整排序带来的与 k 无关的排序成本，改为只选出前 k 个的线性选择。",
  "mechanism": "对输入按关键位分桶，递归只进入包含第 k 大的桶，最终把 top-k 元素提取到输出，保持原 dtype 精度与索引语义；对不适用（n 小、k 接近 n）的 case 回退原排序路径。",
  "name": "ES1 向量排序 route 的 O(N) radix-select 直接选择",
  "op": "top_k",
  "operator_class": "sort-select",
  "operator_scope": "top_k 中 n 与 k 比值大、输入为 ES1 向量排序 route 的 case（避免全量排序、直接选择 top-k 元素）",
  "principle": "当 k 远小于 n 时，完整排序浪费了不必要的比较；按高位桶 radix-select 只在需要的一侧递归，复杂度降到 O(N)，且可利用向量宽度批处理。",
  "related_anti_patterns": [
    "scalar-bounded-heap-fill-finalize",
    "multi-chunk-scalar-bounded-heap"
  ],
  "risks": [
    "分桶退化或桶宽不当会导致接近完整排序，收益消失",
    "边界索引/去重处理错误会引入正确性风险"
  ],
  "slug": "topk-o-n-radix-select-es1-vecsort",
  "source": "run-validated",
  "status": "applied",
  "summary": "对 ES1 向量排序 route 用 O(N) radix-select 直接选出 top-k，替代 O(N log N) 完整排序。",
  "verification": {
    "correctness": [
      "correctness 20/20 pass；verify ok=true"
    ],
    "performance": [
      "incremental 0.9987（3 improved：case17 1.2349x、case8 1.1954x、case12 1.1197x；0 regressed）",
      "官方分 53.0546 → 53.1587（+0.104），post > pre"
    ],
    "rollback_signals": [
      "分桶退化使选择接近完整排序、边界/去重处理出现正确性错误或目标 case 不再落入 ES1 route 时回退原排序路径"
    ]
  }
}
-->

# 性能优化策略：ES1 向量排序 route 的 O(N) radix-select 直接选择

单一优化点：对 ES1 向量排序 route 用 O(N) radix-select 直接选出 top-k，替代 O(N log N) 完整排序。

## 1. 原理

当 k 远小于 n 时，完整排序浪费了不必要的比较；按高位桶 radix-select 只在需要的一侧递归，复杂度降到 O(N)，且可利用向量宽度批处理。

实现机制：对输入按关键位分桶，递归只进入包含第 k 大的桶，最终把 top-k 元素提取到输出，保持原 dtype 精度与索引语义；对不适用（n 小、k 接近 n）的 case 回退原排序路径。

## 2. 性能问题模式

- 优化目标：消除 ES1 向量排序 case 中完整排序带来的与 k 无关的排序成本，改为只选出前 k 个的线性选择。
- 适用数据流：top_k 中 n 与 k 比值大、输入为 ES1 向量排序 route 的 case（避免全量排序、直接选择 top-k 元素）
- Feature signature：`{"bottleneck": ["full-sort-overhead", "k-far-less-than-n"], "dtypes": ["int32", "int64", "fp16", "fp32"], "pattern": "radix-select", "structure": ["vector-sort-route", "bucket-recursion"]}`

## 3. 正确性红线

- 分桶退化或桶宽不当会导致接近完整排序，收益消失
- 边界索引/去重处理错误会引入正确性风险

资源与硬件约束：

- radix 桶宽选择必须匹配向量宽度与内存带宽
- 尾桶处理、索引去重和 top-k 边界必须与 golden 语义一致

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- n/k 比值足够大，使 O(N) 选择相对 O(N log N) 排序有净收益
- 输入为向量排序 route，且 radix 分桶可用向量指令高效表达
- 目标 case 通过运行 routing 落入 ES1 向量排序分支

不适用：

- n 小或 k 接近 n 时选择收益消失，应走原排序
- 非整数/无自然按位序的 dtype 或分桶退化时不用 radix 路径

## 5. 实施步骤

1. 确认 target case 的 runtime route 落在 ES1 向量排序分支
2. 实现按关键位分桶的 radix-select，递归只进包含第 k 大的桶
3. 用向量指令批处理桶内比较，把 top-k 元素提取到输出
4. 对不适用 case 保留原排序回退，验证边界与去重
5. 单 case probe（probe_required）后全量 verify + measure 确认无回归

## 6. LLM 前置问题

- 目标实现是否满足：n/k 比值足够大，使 O(N) 选择相对 O(N log N) 排序有净收益？
- 目标实现是否满足：输入为向量排序 route，且 radix 分桶可用向量指令高效表达？
- 目标实现是否满足：目标 case 通过运行 routing 落入 ES1 向量排序分支？
- 是否命中排除条件：n 小或 k 接近 n 时选择收益消失，应走原排序？

## 7. 验收标准

正确性：

- correctness 20/20 pass；verify ok=true

性能：

- incremental 0.9987（3 improved：case17 1.2349x、case8 1.1954x、case12 1.1197x；0 regressed）
- 官方分 53.0546 → 53.1587（+0.104），post > pre

回滚信号：

- 分桶退化使选择接近完整排序、边界/去重处理出现正确性错误或目标 case 不再落入 ES1 route 时回退原排序路径

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-bounded-heap-fill-finalize, multi-chunk-scalar-bounded-heap

- top_k-20260831_082324-eeb4cf（round=1, status=accepted）

## 检索卡（短卡）

动作：把 ES1 向量排序 route 的完整排序改为按关键位分桶、只递归含第 k 大桶的 O(N) radix-select。
适用：n/k 比值足够大；输入为向量排序 route 且分桶可用向量指令表达；case 落入 ES1 分支。
限制：n 小或 k 接近 n 时收益消失应走原排序；分桶退化会接近完整排序；尾桶/去重/top-k 边界须合 golden。
范围：top_k 中 n 远大于 k 的 ES1 向量排序 case
检索词：radix-select、关键位分桶、桶递归、向量宽度批处理、ES1 向量排序 route
机会：完整排序带来与 k 无关的排序成本
代价：分桶退化或边界/去重错误须回退原排序路径
