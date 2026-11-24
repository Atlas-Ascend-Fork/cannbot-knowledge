---
type: Optimization
title: 微型 shape 的半核与双 tile
description: 每核元素数远小于一次 DMA 往返时，核数减半、每核 2 tile；必须有 ≥2 输入槽。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/micro-shape-half-core-two-tiles.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F8",
  "slug": "micro-shape-half-core-two-tiles",
  "name": "微型 shape 的半核与双 tile",
  "summary": "每核元素数远小于一次 DMA 往返时，核数减半、每核 2 tile；必须有 ≥2 输入槽。",
  "intent": "隐藏微型 shape 的 DMA 往返延迟",
  "mechanism": "当 tilesPerCore=1、每核元素数 ≤4096、总元素数 ≥64K 时，核数减半，重新切 tile 使每核 2 个；第二个 tile 的 MTE2 与第一个 tile 的 VEC/拷出重叠。必须先有 ≥2 输入槽；单槽流水下拆 batch 只增固定开销。微 case 地板/代码体积可能封顶。",
  "principle": "微型 case 的墙钟由一次 MTE2+一次 VEC+一次 MTE3 往返决定，不是吞吐；减少核数让每核多一个 tile，才有重叠机会。",
  "operator_scope": "微型 shape 的核数/占用选择",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "tilesPerCore=1",
      "每核元素数 ≪ 一次 DMA 往返",
      "已有 ≥2 输入槽"
    ],
    "excluded_conditions": [
      "单槽流水",
      "每核元素数较大（吞吐主导）",
      "减核后过载"
    ],
    "constraints": [
      "判据用每核元素数",
      "必须有双输入槽",
      "减核不能损失吞吐",
      "微 case 地板可能封顶"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "dma-roundtrip-latency"
    ],
    "pattern": "micro-shape",
    "reduce_mode": "mixed",
    "structure": [
      "core-count",
      "two-tiles",
      "double-slot"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "算每核元素数与 tilesPerCore",
    "确认已有 ≥2 输入槽",
    "微型档核数减半，重解行批使每核 2 tile",
    "确认第二个 tile 的 MTE2 能提前",
    "按每核元素数设上限，超出回退"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "覆盖最小 shape"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "单槽/非微型/吞吐下降时收紧判据"
    ]
  },
  "risks": [
    "阈值随平台变化",
    "单槽下回退",
    "代码体积影响地板"
  ],
  "gain": "已验证：该机制在目标 A5 算子族上有效，精度 20/20。",
  "generality": "common",
  "classification": "validated_strategy",
  "created": "2026-11-11",
  "evidence": [
    {
      "run_id": "<run-id>",
      "operator_class": "streaming-fusion",
      "status": "accepted",
      "speedup": "validated",
      "precision": "20/20 PASS"
    }
  ],
  "related_anti_patterns": [
    "multi-slot-input-prefetch-with-shape-routing",
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

# 性能优化策略：微型 shape 的半核与双 tile

单一优化点：每核元素数远小于一次 DMA 往返时，核数减半、每核 2 tile；必须有 ≥2 输入槽。

## 1. 原理

微型 case 的墙钟由一次 MTE2+一次 VEC+一次 MTE3 往返决定，不是吞吐；减少核数让每核多一个 tile，才有重叠机会。

实现机制：当 tilesPerCore=1、每核元素数 ≤4096、总元素数 ≥64K 时，核数减半，重新切 tile 使每核 2 个；第二个 tile 的 MTE2 与第一个 tile 的 VEC/拷出重叠。必须先有 ≥2 输入槽；单槽流水下拆 batch 只增固定开销。微 case 地板/代码体积可能封顶。

## 2. 性能问题模式

- 优化目标：隐藏微型 shape 的 DMA 往返延迟
- 适用数据流：微型 shape 的核数/占用选择
- Feature signature：`{"bottleneck": ["dma-roundtrip-latency"], "pattern": "micro-shape", "reduce_mode": "mixed", "structure": ["core-count", "two-tiles", "double-slot"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- 覆盖最小 shape

资源与硬件约束：

- 判据用每核元素数
- 必须有双输入槽
- 减核不能损失吞吐
- 微 case 地板可能封顶

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- tilesPerCore=1
- 每核元素数 ≪ 一次 DMA 往返
- 已有 ≥2 输入槽

不适用：

- 单槽流水
- 每核元素数较大（吞吐主导）
- 减核后过载

## 5. 实施步骤

1. 算每核元素数与 tilesPerCore
2. 确认已有 ≥2 输入槽
3. 微型档核数减半，重解行批使每核 2 tile
4. 确认第二个 tile 的 MTE2 能提前
5. 按每核元素数设上限，超出回退

## 6. LLM 前置问题

- 目标实现是否满足：tilesPerCore=1？
- 目标实现是否满足：每核元素数 ≪ 一次 DMA 往返？
- 目标实现是否满足：已有 ≥2 输入槽？
- 是否命中排除条件：单槽流水？
- 是否命中排除条件：每核元素数较大（吞吐主导）？
- 是否命中排除条件：减核后过载？

## 7. 验收标准

正确性：

- 全量 20/20
- 覆盖最小 shape

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 单槽/非微型/吞吐下降时收紧判据

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：multi-slot-input-prefetch-with-shape-routing、simt-group-occupancy-and-elementwise-replacement

- v3-cardonly-micro-20261111-01（status=accepted, operator_class=streaming-fusion, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：每核元素≤4096、总元素≥64K、tilesPerCore=1时核数减半、每核2tile；必须有≥2输入槽；单槽流水下不要拆。
适用：微型shape，DMA往返主导。
限制：单槽流水下拆batch会回归；微case地板/代码体积可能封顶；每核元素数大的不在域内。
范围：微型shape的核数与tile数选择。
检索词：半核、2tile/核、每核元素数、双输入槽、微case地板、代码体积。
机会：微case路径有效。
代价：分档逻辑；阈值需实测。
