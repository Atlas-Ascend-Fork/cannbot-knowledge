---
type: Optimization
title: 小方阵打包布局、边界与输出 slot
description: h≤8 的小方阵按列打包整组驻留；处理部分列/尾组/负 lane；输出用线性目标索引 + Scatter，避免非 2 的幂除法。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/iterative-small-matrix-packed-layout.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F2",
  "slug": "iterative-small-matrix-packed-layout",
  "name": "小方阵打包布局、边界与输出 slot",
  "summary": "h≤8 的小方阵按列打包整组驻留；处理部分列/尾组/负 lane；输出用线性目标索引 + Scatter，避免非 2 的幂除法。",
  "intent": "降低每轮每寄存器操作数与 UB 往返，同时保证边界正确",
  "mechanism": "每寄存器装 P 列 × M 矩阵（lane=矩阵号×P+列号），整组放 A[R]，group 循环在单 VF；列和跨行逐 lane Add，不做转置 Gather。补齐列/尾组用 validC 掩码保持严格 0；负输入无效 lane 先置 -inf 再做 row max；输出 slot 用 target=slot*m+... 的线性索引 + 寄存器 Scatter，避免 /slot、/mod；输入槽可复用为组尾转置暂存。",
  "principle": "小方阵多轮迭代的成本由每轮寄存器数和每寄存器 op 数决定；列打包让归约向量利用率接近满 lane，并消掉迭代内转置 Gather。",
  "operator_scope": "h≤8 的小方阵多 batch 多轮行列归一化",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "h≤8（h≥9 的 R=h·ceil(h/P) 不可行）",
      "整组矩阵与统计量能装进寄存器",
      "工具链支持寄存器数组（先穿刺）"
    ],
    "excluded_conditions": [
      "h≥9（R=24/36 不可行，改用行槽+交错）",
      "寄存器溢出/spill",
      "跨 tile/跨核必须经 UB 交接的中间量"
    ],
    "constraints": [
      "部分列/尾组用 validC 严格 0",
      "负 lane 先置 -inf",
      "Scatter 基址按实际 slot 栅格（如 40m 而非 48m）；-inf pad 在 ExpSub MERGING 下要显式清零",
      "非 2 的幂 slot 用线性目标索引，避免 /slot"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "ub-roundtrip",
      "ops-per-register",
      "layout"
    ],
    "pattern": "small-matrix-packing",
    "reduce_mode": "row-col",
    "structure": [
      "packed-layout",
      "whole-group-residency",
      "validC",
      "linear-slot-index"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "按 h 选 P：h≤4→P=4，h=5..8→P=4/8；算 R=h·ceil(h/P) 与寄存器预算",
    "整组放 A[R]，group 循环进单 VF，迭代内零 UB 往返",
    "部分列/尾组用 validC；负 lane 先置 -inf",
    "输出用 target=slot*m+... 线性索引 + Scatter",
    "与 padded 路径逐 h/iter A/B；h≥9 回退行槽"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "n=3/6 部分列与 40-float slot 正确",
      "负输入/NaN/Inf 覆盖"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "边界数值错误、slot 错位或 h≥9 时回退 padded/行槽"
    ]
  },
  "risks": [
    "寄存器/索引表压力",
    "部分列/尾组易静默错",
    "h≥9 不可用"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "small-matrix-iteration",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "small-matrix-bulk-compact-copy",
    "simt-group-occupancy-and-elementwise-replacement"
  ],
  "related_seed_ids": [],
  "instance_ids": [],
  "source": "benchmark-extraction",
  "status": "validated",
  "provenance": {
    "skill": "validated-optimization-extraction-20261111"
  }
}
-->

# 性能优化策略：小方阵打包布局、边界与输出 slot

单一优化点：h≤8 的小方阵按列打包整组驻留；处理部分列/尾组/负 lane；输出用线性目标索引 + Scatter，避免非 2 的幂除法。

## 1. 原理

小方阵多轮迭代的成本由每轮寄存器数和每寄存器 op 数决定；列打包让归约向量利用率接近满 lane，并消掉迭代内转置 Gather。

实现机制：每寄存器装 P 列 × M 矩阵（lane=矩阵号×P+列号），整组放 A[R]，group 循环在单 VF；列和跨行逐 lane Add，不做转置 Gather。补齐列/尾组用 validC 掩码保持严格 0；负输入无效 lane 先置 -inf 再做 row max；输出 slot 用 target=slot*m+... 的线性索引 + 寄存器 Scatter，避免 /slot、/mod；输入槽可复用为组尾转置暂存。

## 2. 性能问题模式

- 优化目标：降低每轮每寄存器操作数与 UB 往返，同时保证边界正确
- 适用数据流：h≤8 的小方阵多 batch 多轮行列归一化
- Feature signature：`{"bottleneck": ["ub-roundtrip", "ops-per-register", "layout"], "pattern": "small-matrix-packing", "reduce_mode": "row-col", "structure": ["packed-layout", "whole-group-residency", "validC", "linear-slot-index"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- n=3/6 部分列与 40-float slot 正确
- 负输入/NaN/Inf 覆盖

资源与硬件约束：

- 部分列/尾组用 validC 严格 0
- 负 lane 先置 -inf
- Scatter 基址按实际 slot 栅格（如 40m 而非 48m）；-inf pad 在 ExpSub MERGING 下要显式清零
- 非 2 的幂 slot 用线性目标索引，避免 /slot

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- h≤8（h≥9 的 R=h·ceil(h/P) 不可行）
- 整组矩阵与统计量能装进寄存器
- 工具链支持寄存器数组（先穿刺）

不适用：

- h≥9（R=24/36 不可行，改用行槽+交错）
- 寄存器溢出/spill
- 跨 tile/跨核必须经 UB 交接的中间量

## 5. 实施步骤

1. 按 h 选 P：h≤4→P=4，h=5..8→P=4/8；算 R=h·ceil(h/P) 与寄存器预算
2. 整组放 A[R]，group 循环进单 VF，迭代内零 UB 往返
3. 部分列/尾组用 validC；负 lane 先置 -inf
4. 输出用 target=slot*m+... 线性索引 + Scatter
5. 与 padded 路径逐 h/iter A/B；h≥9 回退行槽

## 6. LLM 前置问题

- 目标实现是否满足：h≤8（h≥9 的 R=h·ceil(h/P) 不可行）？
- 目标实现是否满足：整组矩阵与统计量能装进寄存器？
- 目标实现是否满足：工具链支持寄存器数组（先穿刺）？
- 是否命中排除条件：h≥9（R=24/36 不可行，改用行槽+交错）？
- 是否命中排除条件：寄存器溢出/spill？
- 是否命中排除条件：跨 tile/跨核必须经 UB 交接的中间量？

## 7. 验收标准

正确性：

- 全量 20/20
- n=3/6 部分列与 40-float slot 正确
- 负输入/NaN/Inf 覆盖

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 边界数值错误、slot 错位或 h≥9 时回退 padded/行槽

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：small-matrix-bulk-compact-copy、simt-group-occupancy-and-elementwise-replacement

- v4-cardonly-packed-20261111-01（status=accepted, operator_class=small-matrix-iteration, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：h≤8小方阵按列打包整组驻留；部分列/尾组用validC，负lane先置-inf；输出用线性目标索引+Scatter，避免/slot。
适用：h≤8的小方阵多batch多轮行列归一化。
限制：h≥9的R=24/36不可行；Scatter基址按实际slot栅格；-inf pad在ExpSub MERGING下要显式清零。
范围：小方阵打包布局、边界与输出slot。
检索词：列打包、整组驻留、validC、-inf、Scatter、40-float slot、线性目标索引、h≤8。
机会：列打包在目标小方阵shape上有效；槽复用省一次InitBuffer。
代价：寄存器/索引表压力；h≥9不可用；边界多需逐shape验证。
