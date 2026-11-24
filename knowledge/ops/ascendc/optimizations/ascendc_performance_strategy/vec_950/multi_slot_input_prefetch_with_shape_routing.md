---
type: Optimization
title: 输入多槽、预取前移与按 shape 路由
description: 输入 ≥2 槽，预取前移到最后一个输入消费者之后；仅当不缩小行批时启用；钳位后重算可行性并补 MTE2→V 同步。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/multi-slot-input-prefetch-with-shape-routing.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "schema_version": 2,
  "id": "F4",
  "slug": "multi-slot-input-prefetch-with-shape-routing",
  "name": "输入多槽、预取前移与按 shape 路由",
  "summary": "输入 ≥2 槽，预取前移到最后一个输入消费者之后；仅当不缩小行批时启用；钳位后重算可行性并补 MTE2→V 同步。",
  "intent": "让 MTE2 与 VEC/MTE3 重叠，同时不牺牲行批",
  "mechanism": "输入队列 ≥2 槽，事件池按槽管理 MTE2→V 与 V→MTE2；当前 tile 的最后一个输入消费者结束后立即发下一 tile 的 MTE2。只有双槽不缩小行批（aSlots2==aSlots1）且 tilesPerCore≥2 时启用；否则单槽。共享输出槽/输入槽复用时延迟等待保在途安全。tiling 钳位到 a=1 后重算常驻缓冲可行性；常驻预转前显式 MTE2→V 同步。",
  "principle": "单槽时 MTE2(t+1) 必须等 V(t) 与 MTE3(t) 结束；双槽把搬入藏到计算后面。但双槽挤小行批时，每 tile 固定成本会吃掉收益。",
  "operator_scope": "每 tile 搬入→计算→搬出的流式 kernel",
  "operator_class": "",
  "op": "seed",
  "applicability": {
    "required_conditions": [
      "每核至少 2 个 tile",
      "输入槽可独立寻址",
      "UB 能放下 ≥2 槽且不缩小行批"
    ],
    "excluded_conditions": [
      "tilesPerCore<2",
      "双槽会缩小行批",
      "输入槽存在跨 tile 复用依赖"
    ],
    "constraints": [
      "仅 aSlots2==aSlots1 用双槽",
      "预取点在最后一个输入消费者之后",
      "槽位复用须证在途安全",
      "钳位后重算可行性；常驻预转补 MTE2→V"
    ]
  },
  "applicability_boundary": "",
  "feature_signature": {
    "bottleneck": [
      "mte2-vec-serial",
      "ub-budget"
    ],
    "pattern": "streaming-pipeline",
    "reduce_mode": "mixed",
    "structure": [
      "multi-slot",
      "prefetch",
      "shape-route",
      "mte2-v-sync"
    ],
    "dtypes": []
  },
  "implementation_steps": [
    "把输入队列改 ≥2 槽，按槽建事件池",
    "确定当前 tile 的最后一个输入消费者",
    "在其后立即发下一 tile 的 MTE2",
    "按 aSlots2==aSlots1 与 tilesPerCore 路由槽数",
    "末尾 nBuf 个 tile 跳过预取，收尾事件"
  ],
  "verification": {
    "correctness": [
      "全量 20/20",
      "槽位 WAR/RAW 覆盖最后 tile",
      "钳位后无越界/device error"
    ],
    "performance": [
      "相对基线有可测提升；具体数值不在卡内给出",
      "关键 shape 不回归"
    ],
    "rollback_signals": [
      "槽位竞态、精度失败或行批缩水时回退单槽"
    ]
  },
  "risks": [
    "UB 挤压行批",
    "预取点选错",
    "小 shape 固定开销"
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
    "single-pass-fused-statistics-chain",
    "micro-shape-half-core-two-tiles"
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

# 性能优化策略：输入多槽、预取前移与按 shape 路由

单一优化点：输入 ≥2 槽，预取前移到最后一个输入消费者之后；仅当不缩小行批时启用；钳位后重算可行性并补 MTE2→V 同步。

## 1. 原理

单槽时 MTE2(t+1) 必须等 V(t) 与 MTE3(t) 结束；双槽把搬入藏到计算后面。但双槽挤小行批时，每 tile 固定成本会吃掉收益。

实现机制：输入队列 ≥2 槽，事件池按槽管理 MTE2→V 与 V→MTE2；当前 tile 的最后一个输入消费者结束后立即发下一 tile 的 MTE2。只有双槽不缩小行批（aSlots2==aSlots1）且 tilesPerCore≥2 时启用；否则单槽。共享输出槽/输入槽复用时延迟等待保在途安全。tiling 钳位到 a=1 后重算常驻缓冲可行性；常驻预转前显式 MTE2→V 同步。

## 2. 性能问题模式

- 优化目标：让 MTE2 与 VEC/MTE3 重叠，同时不牺牲行批
- 适用数据流：每 tile 搬入→计算→搬出的流式 kernel
- Feature signature：`{"bottleneck": ["mte2-vec-serial", "ub-budget"], "pattern": "streaming-pipeline", "reduce_mode": "mixed", "structure": ["multi-slot", "prefetch", "shape-route", "mte2-v-sync"], "dtypes": []}`

## 3. 正确性红线

- 全量 20/20
- 槽位 WAR/RAW 覆盖最后 tile
- 钳位后无越界/device error

资源与硬件约束：

- 仅 aSlots2==aSlots1 用双槽
- 预取点在最后一个输入消费者之后
- 槽位复用须证在途安全
- 钳位后重算可行性；常驻预转补 MTE2→V

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 每核至少 2 个 tile
- 输入槽可独立寻址
- UB 能放下 ≥2 槽且不缩小行批

不适用：

- tilesPerCore<2
- 双槽会缩小行批
- 输入槽存在跨 tile 复用依赖

## 5. 实施步骤

1. 把输入队列改 ≥2 槽，按槽建事件池
2. 确定当前 tile 的最后一个输入消费者
3. 在其后立即发下一 tile 的 MTE2
4. 按 aSlots2==aSlots1 与 tilesPerCore 路由槽数
5. 末尾 nBuf 个 tile 跳过预取，收尾事件

## 6. LLM 前置问题

- 目标实现是否满足：每核至少 2 个 tile？
- 目标实现是否满足：输入槽可独立寻址？
- 目标实现是否满足：UB 能放下 ≥2 槽且不缩小行批？
- 是否命中排除条件：tilesPerCore<2？
- 是否命中排除条件：双槽会缩小行批？
- 是否命中排除条件：输入槽存在跨 tile 复用依赖？

## 7. 验收标准

正确性：

- 全量 20/20
- 槽位 WAR/RAW 覆盖最后 tile
- 钳位后无越界/device error

性能：

- 相对基线有可测提升；具体数值不在卡内给出
- 关键 shape 不回归

回滚信号：

- 槽位竞态、精度失败或行批缩水时回退单槽

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related strategies：single-pass-fused-statistics-chain、micro-shape-half-core-two-tiles

- v3-cardonly-prefetch-20261111-01（status=accepted, operator_class=streaming-fusion, speedup=validated, precision=20/20 PASS）

## 检索卡（短卡）

动作：输入≥2槽，预取前移到该tile最后一个输入消费者之后；仅当双槽不缩小行批时启用；tilesPerCore<2不预取；钳位后重算可行性并补MTE2→V同步。
适用：每tile搬入→计算→搬出的流式kernel。
限制：无条件双槽会缩小行批并回退；每核仅1tile无预取；共享槽需延迟等待保在途安全。
范围：流式kernel的输入槽、预取点与shape路由。
检索词：输入多槽、预取前移、行批不缩水、tilesPerCore、钳位可行性、MTE2→V同步。
机会：宽shape上双槽预取有效；路由把无条件双槽的收益修正回来。
代价：UB挤压行批；槽位生命周期；小shape固定开销。
