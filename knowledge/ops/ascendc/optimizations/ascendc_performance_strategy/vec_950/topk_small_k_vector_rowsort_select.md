---
type: Optimization
title: 小 k 比下整行向量排序选择（gating dataflow，SIMT 选择排序消除 + host 去钳位）
description: 把逐元素 SIMT 选择排序（逐候选线性扫描 + k 次选择循环）替换为 AscendC::Sort<T,true> 整行向量排序 + 一次 top-k 截取（值+索引），并解除 host 侧对行块规模的钳位，使 kernel 能按整行块消费输入。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/topk-small-k-vector-rowsort-select.md
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
      "UB 峰值须按整行×行块重新核算（host tiling 与 kernel Init 逐项对应）",
      "官方 correctness 判据决定平局敏感输出（如 expert_idx 类位置输出）是否参与比较；strict pytest 若用 CPU golden 的平局置换会产生与基线相同的既有分歧，须按官方判据裁决"
    ],
    "excluded_conditions": [
      "行无法驻留 UB 需分 chunk 归并（见 chunked-vector-sort-merge 类卡）",
      "排序稳定性/平局次序有输出契约且与硬件排序平局规则冲突（需官方判据不比较受影响输出）"
    ],
    "required_conditions": [
      "行内元素可整行（或行块）驻留 UB",
      "每行独立选 top-k（无跨行依赖），比较语义可由排序比较器表达",
      "dtype 支持整行向量排序（half/bf16/fp32 类）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "5aac23d893cbae55b88ae2df641658d2b611aa07872f9bbe3d94e0f0a0957d64",
      "decision_sha256": "40d86246bcfcaf2e4070858c5db75130281e514c763a48a95d25979c2ebde968",
      "incremental_sha256": "35a74269dea9bf8a36ab731ea87c5e37f58bd64169235ade06981a6f23ff72f3",
      "operator_class": "layout-transform",
      "performance_sha256": "1f0744eae4d7413577d137864aeeced7739a6ff3f50264d0a949f865e0b02f91",
      "precision": "官方判据 20/20 PASS；strict pytest 6/20 失败为基线既有 golden torch.topk 平局置换分歧（expert_idx compare:false），逐 case 与基线相同",
      "round": 1,
      "run_id": "<run-id>",
      "speedup": "incremental 409.54x（验证 8 case：2.37x–2830.7x）；final 官方口径 20/20 improved，累计 395.70x，官方分 53.04→68.38（+15.35）",
      "status": "accepted",
      "strategy_sha256": "1706688983d469943420fd2294209bbaf106a9d8650c4ed348d996b9403c36f8",
      "verify_sha256": "158c10cb508954def8d70a6f2b9ae68c442a3f7b9ec92f41ff91d2da0218fa4f"
    },
    {
      "comparison_sha256": "5aac23d893cbae55b88ae2df641658d2b611aa07872f9bbe3d94e0f0a0957d64",
      "decision_sha256": "40d86246bcfcaf2e4070858c5db75130281e514c763a48a95d25979c2ebde968",
      "operator_class": "layout-transform",
      "performance_sha256": "1f0744eae4d7413577d137864aeeced7739a6ff3f50264d0a949f865e0b02f91",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "1706688983d469943420fd2294209bbaf106a9d8650c4ed348d996b9403c36f8",
      "verify_sha256": "158c10cb508954def8d70a6f2b9ae68c442a3f7b9ec92f41ff91d2da0218fa4f"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-steady-state-linear-scan",
      "per-row-k-selection-loop"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "small-k-whole-row-vector-sort-select"
  },
  "generality": "op_class",
  "id": "TOPK-SMALLK-VECTOR-ROWSORT-SELECT",
  "implementation_steps": [
    "定位逐元素选择/堆扫描热点（op_summary 的 Scalar/vec 占比 + 源码逐元素循环）",
    "在值域计算后插入整行 Sort<T,true>（带索引），删除 SIMT 选择循环",
    "从有序段截取前 k 个值+索引，接续原输出链",
    "host 侧解除行块钳位并重算 UB 预算，逐项更新 tiling",
    "全量 verify（官方判据）+ 增量/累计测量 + 大加速 case 官方路径抽查"
  ],
  "intent": "消除 AIV Scalar 管线被逐元素比较/选择循环支配的瓶颈（rows_per_core·k·E 量级的标量访存-比较序列）。",
  "mechanism": "kernel：值域计算后直接对整行（或行块拼接的连续段）调用 AscendC::Sort<T,true>（fp32 值 + 硬件索引追踪），排序后从头部截取 k 个（值与索引），再走既有的输出/归一化尾链。host：移除把行块规模钳到很小值的参数钳位（F_MAX 类），CalcUbBytes/Init 按新 UB 峰值逐项更新。",
  "name": "小 k 比下整行向量排序选择（gating dataflow，SIMT 选择排序消除 + host 去钳位）",
  "operator_class": "layout-transform",
  "operator_scope": "归一化值域（softmax/exp 链）后按行选 top-k 的融合选择类 dataflow；行内元素可整行驻留 UB，行按块（多行/迭代）组织",
  "principle": "标量选择排序的复杂度随 k·E 线性放大且逐元素占用 Scalar issue；向量整行排序一次 V-pipe 通行完成全局有序化，k 只是输出截取宽度，与排序成本解耦，因此 k/E 很小时收益反而最大。",
  "related_anti_patterns": [
    "scalar-steady-state-linear-scan"
  ],
  "risks": [
    "平局次序与 CPU golden 的 topk 平局置换分歧：需确认官方判据对位置类输出的比较开关",
    "UB 峰值核算遗漏导致越界或回退"
  ],
  "slug": "topk-small-k-vector-rowsort-select",
  "summary": "把逐元素 SIMT 选择排序（逐候选线性扫描 + k 次选择循环）替换为 AscendC::Sort<T,true> 整行向量排序 + 一次 top-k 截取（值+索引），并解除 host 侧对行块规模的钳位，使 kernel 能按整行块消费输入。",
  "verification": {
    "correctness": [
      "官方判据全过（本轮 20/20，值输出 ≤1 dtype ulp；位置类输出按 proto compare 开关豁免）",
      "strict pytest 失败集若为既有 golden 平局置换类，须与基线失败集逐 case 相同"
    ],
    "performance": [
      "增量 total_speedup 显著 >1（本轮验证集 3 个数量级）；控制 case 无超阈值回归",
      "大加速（>1.2x）须过官方路径 spot_check 复测"
    ],
    "rollback_signals": [
      "官方判据出现值输出失配",
      "控制 case 回归超 run 阈值且非噪声地板",
      "spot_check 不可复现"
    ]
  }
}
-->

# 性能优化策略：小 k 比下整行向量排序选择（gating dataflow，SIMT 选择排序消除 + host 去钳位）

单一优化点：把逐元素 SIMT 选择排序（逐候选线性扫描 + k 次选择循环）替换为 AscendC::Sort<T,true> 整行向量排序 + 一次 top-k 截取（值+索引），并解除 host 侧对行块规模的钳位，使 kernel 能按整行块消费输入。

## 1. 原理

标量选择排序的复杂度随 k·E 线性放大且逐元素占用 Scalar issue；向量整行排序一次 V-pipe 通行完成全局有序化，k 只是输出截取宽度，与排序成本解耦，因此 k/E 很小时收益反而最大。

实现机制：kernel：值域计算后直接对整行（或行块拼接的连续段）调用 AscendC::Sort<T,true>（fp32 值 + 硬件索引追踪），排序后从头部截取 k 个（值与索引），再走既有的输出/归一化尾链。host：移除把行块规模钳到很小值的参数钳位（F_MAX 类），CalcUbBytes/Init 按新 UB 峰值逐项更新。

## 2. 性能问题模式

- 优化目标：消除 AIV Scalar 管线被逐元素比较/选择循环支配的瓶颈（rows_per_core·k·E 量级的标量访存-比较序列）。
- 适用数据流：归一化值域（softmax/exp 链）后按行选 top-k 的融合选择类 dataflow；行内元素可整行驻留 UB，行按块（多行/迭代）组织
- Feature signature：`{"bottleneck": ["scalar-steady-state-linear-scan", "per-row-k-selection-loop"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "small-k-whole-row-vector-sort-select"}`

## 3. 正确性红线

- 平局次序与 CPU golden 的 topk 平局置换分歧：需确认官方判据对位置类输出的比较开关
- UB 峰值核算遗漏导致越界或回退

资源与硬件约束：

- UB 峰值须按整行×行块重新核算（host tiling 与 kernel Init 逐项对应）
- 官方 correctness 判据决定平局敏感输出（如 expert_idx 类位置输出）是否参与比较；strict pytest 若用 CPU golden 的平局置换会产生与基线相同的既有分歧，须按官方判据裁决

## 4. 泛化条件

- 策略作用域：op_class：layout-transform

适用：

- 行内元素可整行（或行块）驻留 UB
- 每行独立选 top-k（无跨行依赖），比较语义可由排序比较器表达
- dtype 支持整行向量排序（half/bf16/fp32 类）

不适用：

- 行无法驻留 UB 需分 chunk 归并（见 chunked-vector-sort-merge 类卡）
- 排序稳定性/平局次序有输出契约且与硬件排序平局规则冲突（需官方判据不比较受影响输出）

## 5. 实施步骤

1. 定位逐元素选择/堆扫描热点（op_summary 的 Scalar/vec 占比 + 源码逐元素循环）
2. 在值域计算后插入整行 Sort<T,true>（带索引），删除 SIMT 选择循环
3. 从有序段截取前 k 个值+索引，接续原输出链
4. host 侧解除行块钳位并重算 UB 预算，逐项更新 tiling
5. 全量 verify（官方判据）+ 增量/累计测量 + 大加速 case 官方路径抽查

## 6. LLM 前置问题

- 目标实现是否满足：行内元素可整行（或行块）驻留 UB？
- 目标实现是否满足：每行独立选 top-k（无跨行依赖），比较语义可由排序比较器表达？
- 目标实现是否满足：dtype 支持整行向量排序（half/bf16/fp32 类）？
- 是否命中排除条件：行无法驻留 UB 需分 chunk 归并（见 chunked-vector-sort-merge 类卡）？

## 7. 验收标准

正确性：

- 官方判据全过（本轮 20/20，值输出 ≤1 dtype ulp；位置类输出按 proto compare 开关豁免）
- strict pytest 失败集若为既有 golden 平局置换类，须与基线失败集逐 case 相同

性能：

- 增量 total_speedup 显著 >1（本轮验证集 3 个数量级）；控制 case 无超阈值回归
- 大加速（>1.2x）须过官方路径 spot_check 复测

回滚信号：

- 官方判据出现值输出失配
- 控制 case 回归超 run 阈值且非噪声地板
- spot_check 不可复现

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：scalar-steady-state-linear-scan

- moe_gating_top_k_softmax-20260901_132104-d2096f（round=1, status=accepted, speedup=incremental 409.54x（验证 8 case：2.37x–2830.7x）；final 官方口径 20/20 improved，累计 395.70x，官方分 53.04→68.38（+15.35））
- moe_gating_top_k_softmax-20260901_132104-d2096f（round=1, status=accepted）

## 检索卡（短卡）

动作：把逐元素 SIMT 选择排序替换为 AscendC::Sort<T,true> 整行向量排序加一次 top-k 截取，并解除 host 行块钳位。
适用：行内元素可整行或行块驻留 UB；每行独立选 top-k；dtype 支持整行向量排序（half/bf16/fp32）。
限制：平局次序与 CPU golden 的 topk 置换有分歧，须确认官方判据对位置类输出的比较开关；UB 峰值须重新核算。
范围：归一化值域后按行选 top-k 的融合选择 dataflow
检索词：AscendC::Sort<T,true>、整行向量排序、top-k 截取、host 去钳位、F_MAX、CalcUbBytes
机会：AIV Scalar 被逐元素比较/选择循环支配
