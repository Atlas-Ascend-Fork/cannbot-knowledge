---
type: Optimization
title: 欠并行索引轴的逻辑行扩展切分
description: 将索引前缀行并入逻辑任务空间，修复短 outer 轴导致的多核欠利用。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/underfilled-axis-row-parallel-tiling.md
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
      "扩展后的逻辑行映射必须能由既有 stride 字段无歧义表达，所有乘法使用宽整数防溢出",
      "被并入的索引前缀维不能引入跨行写冲突或改变输出线性顺序"
    ],
    "excluded_conditions": [
      "索引行之间存在依赖、输出需要归约冲突处理，或 kernel 不能表达零源行 stride 时不适用",
      "原切分轴已经足以占满核心或行粒度过小导致调度成本主导时无需启用"
    ],
    "required_conditions": [
      "原 tiling 只沿 outer 维分核且 outer 小于可用核数",
      "索引张量存在可独立的前缀行维，可与 outer 合并成更大的逻辑行空间",
      "单个逻辑行的 gather 语义和地址映射在合并后保持不变"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 27.6,
      "before_us": 1494.3,
      "case": "1",
      "operator_class": "index-gather",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/gather/<run-id>/phase6_apply/final_report.md",
      "speedup": 54.2,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "tiling-axis"
    ],
    "dtypes": [],
    "pattern": "underfilled-axis-row-parallel",
    "reduce_mode": "indexed-read",
    "structure": [
      "host-tiling",
      "logical-row",
      "axis-flatten"
    ]
  },
  "gain": "case_1 1494.3→27.6us（54.2x），case_5 85204→1494.9us（57.0x）；非触发 case_10 持平。",
  "generality": "op_class",
  "id": "G3-UnderfilledAxisParallel",
  "implementation_steps": [
    "在 host 侧计算原切分空间 outer 与可用核数，识别欠并行形状",
    "证明索引前缀行彼此独立后，将 outer 与 gather 行数展平为逻辑行总数",
    "重写逻辑行到输入/索引/输出基址的 stride 参数，让 kernel 每次仍处理一个普通行",
    "仅对欠并行且映射可证明的形状设置新 tiling key，其他形状保持旧路径",
    "验证边界行、尾核、不同 dim 和大索引张量的地址范围"
  ],
  "intent": "解决 Gather 仅沿很短的 outer 轴分核导致绝大多数核心空闲的问题。",
  "mechanism": "host 将 outer 与索引前缀行数合并为 outer×gatherRows 个逻辑行，并通过行数与 stride 字段把每个逻辑行映射回原输入；kernel 继续按单行 gather 执行，无需改变核心计算。",
  "name": "欠并行索引轴的逻辑行扩展切分",
  "op": "gather",
  "operator_class": "index-gather",
  "operator_scope": "outer 维很短、但索引前缀中存在大量独立行的 Gather 类 indexed-read 数据流",
  "principle": "并行度由 tiling 选择的逻辑任务数决定，而不必局限于原张量的单一轴；把可独立的索引行并入任务空间，可在不改变每行 kernel 语义的情况下占满核心。",
  "provenance": {
    "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/gather/<run-id>/phase6_apply/final_report.md"
  },
  "related_anti_patterns": [
    "tile-ub-budget-mismatch"
  ],
  "risks": [
    "逻辑行到物理行的 stride 推导错误会导致跨行读取或写错输出",
    "任务数乘积和地址偏移溢出可能只在大 shape 上暴露"
  ],
  "schema_version": 2,
  "slug": "underfilled-axis-row-parallel-tiling",
  "source": "external_verified",
  "status": "applied",
  "summary": "将索引前缀行并入逻辑任务空间，修复短 outer 轴导致的多核欠利用。",
  "verification": {
    "correctness": [
      "覆盖 dim=0 与非零 dim、单/多索引行、尾核、不同 index dtype 和大偏移，并执行全量精度测试"
    ],
    "performance": [
      "比较 outer<coreNum 的触发形状与原本已饱和的非触发形状，确认核心利用率提升且回退无回归"
    ],
    "rollback_signals": [
      "出现跨行错位、地址溢出、写冲突或非触发路径稳定回归时回退"
    ]
  }
}
-->

# 性能优化策略：欠并行索引轴的逻辑行扩展切分

单一优化点：将索引前缀行并入逻辑任务空间，修复短 outer 轴导致的多核欠利用。

## 1. 原理

并行度由 tiling 选择的逻辑任务数决定，而不必局限于原张量的单一轴；把可独立的索引行并入任务空间，可在不改变每行 kernel 语义的情况下占满核心。

实现机制：host 将 outer 与索引前缀行数合并为 outer×gatherRows 个逻辑行，并通过行数与 stride 字段把每个逻辑行映射回原输入；kernel 继续按单行 gather 执行，无需改变核心计算。

## 2. 性能问题模式

- 优化目标：解决 Gather 仅沿很短的 outer 轴分核导致绝大多数核心空闲的问题。
- 适用数据流：outer 维很短、但索引前缀中存在大量独立行的 Gather 类 indexed-read 数据流
- Feature signature：`{"bottleneck": ["core-underutilization", "tiling-axis"], "dtypes": [], "pattern": "underfilled-axis-row-parallel", "reduce_mode": "indexed-read", "structure": ["host-tiling", "logical-row", "axis-flatten"]}`

## 3. 正确性红线

- 逻辑行到物理行的 stride 推导错误会导致跨行读取或写错输出
- 任务数乘积和地址偏移溢出可能只在大 shape 上暴露

资源与硬件约束：

- 扩展后的逻辑行映射必须能由既有 stride 字段无歧义表达，所有乘法使用宽整数防溢出
- 被并入的索引前缀维不能引入跨行写冲突或改变输出线性顺序

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 原 tiling 只沿 outer 维分核且 outer 小于可用核数
- 索引张量存在可独立的前缀行维，可与 outer 合并成更大的逻辑行空间
- 单个逻辑行的 gather 语义和地址映射在合并后保持不变

不适用：

- 索引行之间存在依赖、输出需要归约冲突处理，或 kernel 不能表达零源行 stride 时不适用
- 原切分轴已经足以占满核心或行粒度过小导致调度成本主导时无需启用

## 5. 实施步骤

1. 在 host 侧计算原切分空间 outer 与可用核数，识别欠并行形状
2. 证明索引前缀行彼此独立后，将 outer 与 gather 行数展平为逻辑行总数
3. 重写逻辑行到输入/索引/输出基址的 stride 参数，让 kernel 每次仍处理一个普通行
4. 仅对欠并行且映射可证明的形状设置新 tiling key，其他形状保持旧路径
5. 验证边界行、尾核、不同 dim 和大索引张量的地址范围

## 6. LLM 前置问题

- 目标实现是否满足：原 tiling 只沿 outer 维分核且 outer 小于可用核数？
- 目标实现是否满足：索引张量存在可独立的前缀行维，可与 outer 合并成更大的逻辑行空间？
- 目标实现是否满足：单个逻辑行的 gather 语义和地址映射在合并后保持不变？
- 是否命中排除条件：索引行之间存在依赖、输出需要归约冲突处理，或 kernel 不能表达零源行 stride 时不适用？

## 7. 验收标准

正确性：

- 覆盖 dim=0 与非零 dim、单/多索引行、尾核、不同 index dtype 和大偏移，并执行全量精度测试

性能：

- 比较 outer<coreNum 的触发形状与原本已饱和的非触发形状，确认核心利用率提升且回退无回归

回滚信号：

- 出现跨行错位、地址溢出、写冲突或非触发路径稳定回归时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：tile-ub-budget-mismatch

- ksearch-gather-<run-id>（status=accepted, case=1, speedup=54.2）

## 检索卡（短卡）

动作：将 outer 与独立索引前缀行合并为 outer×gatherRows 个逻辑任务，保持每行语义
适用：仅沿短 outer 分核，且索引前缀行彼此独立、可与 outer 合并
限制：逻辑行映射须由既有 stride 无歧义表达；乘法使用宽整数防溢出
范围：index-gather 的 Gather 类 indexed-read 数据流
检索词：Gather、outer、gatherRows、逻辑行、stride、欠并行
机会：Gather 仅沿很短 outer 轴分核，绝大多数核心空闲
