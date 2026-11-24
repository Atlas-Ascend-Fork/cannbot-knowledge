---
type: Optimization
title: S_MTE3 事件同步在 MIX_AIV_1_0 + 硬 SyncAll 上下文触发设备 507035
description: 在MIX_AIV_1_0加硬SyncAll归并中禁用该事件组合，并以可证明的同步保持聚合写到读可见性。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/s-mte3-event-mix-syncall-error.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "分离模式（MIX_AIV_1_0）多核归约的聚合写->读可见性用 PipeBarrier<PIPE_ALL>，勿用 S_MTE3 事件",
      "读侧（MTE2_S）同步同疑，保留 PipeBarrier",
      "用 A/B 二分（build1/build2）确认 507035 归因，不要直接改同步方案"
    ],
    "excluded_conditions": [
      "纯 AIV 或无线程级跨核归并场景可继续用 S_MTE3（group_norm.h 同模式实测可用）"
    ],
    "required_conditions": [
      "两阶段跨核归约需保证聚合 val/idx 的跨核可见性（Pass1 写 -> Pass2 读）",
      "kernel 采用 KERNEL_TYPE_MIX_AIV_1_0 且两阶段间使用 SyncAll() 硬同步"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "case": "13",
      "env": {
        "device": "5",
        "op_name": "Cummin",
        "post_eval_score": 60.87859925160219,
        "pre_eval_score": 57.42744371577807,
        "score_delta": "+3.45"
      },
      "operator_class": "reduction",
      "precision": "20/20 passed after rollback",
      "run_id": "<run-id>",
      "status": "rejected",
      "task_dir": "cann-bench_rpy/strategies/cummin_opt_20260821"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "cross-core-visibility",
      "sync-primitive-selection"
    ],
    "error": [
      "507035-npu-sync-failure"
    ],
    "pattern": "s-mte3-event-incompatible-with-mix-syncall",
    "structure": [
      "scalar-to-mte3-event",
      "mix-aiv-task",
      "hard-syncall",
      "cross-core-aggregate"
    ]
  },
  "generality": "op_class",
  "id": "NEG-S-MTE3-MIX-SYNCALL",
  "implementation_steps": [
    "识别跨核归约聚合写->读可见性需求，评估同步原语选型",
    "勿在 MIX_AIV_1_0 + 硬 SyncAll 上下文使用 S_MTE3/MTE2_S 事件同步",
    "写侧用 PipeBarrier<PIPE_ALL> 排序，读侧保留 PipeBarrier",
    "用 A/B 二分（build1/build2）确认 507035 归因后再定稿同步方案"
  ],
  "intent": "保证两阶段跨核扫描中 Pass2 能读到 Pass1 写出的聚合 val/idx（避免用全局 PipeBarrier 的粗粒度同步）。",
  "mechanism": "S_MTE3 SetFlag/WaitFlag 试图把标量写与 MTE3 读排序；在 KERNEL_TYPE_MIX_AIV_1_0 + SyncAll() 下触发设备 507035（NPU sync 失败，异步 sticky）。build1/build2 二分证实为 S_MTE3 所致；移除后 bisect2 通过。写侧回退 PipeBarrier<PIPE_ALL>，读侧（MTE2_S）同疑保留 PipeBarrier。",
  "name": "S_MTE3 事件同步在 MIX_AIV_1_0 + 硬 SyncAll 上下文触发设备 507035",
  "operator_class": "reduction",
  "operator_scope": "跨核归约中 Scalar->MTE3 事件同步（S_MTE3 SetFlag/WaitFlag）与 KERNEL_TYPE_MIX_AIV_1_0 + 硬 SyncAll() 组合，用于保证聚合 val/idx 的跨核可见性",
  "principle": "跨流水事件标志（S_MTE3/MTE2_S）与 MIX+硬 SyncAll 的线程级跨核归并组合不兼容；同一模式在纯 AIV 或无线程级跨核归并场景可用（如 group_norm.h），不可直接照搬到需要硬 SyncAll 的多核归约。",
  "related_anti_patterns": [],
  "risks": [
    "在 MIX+硬 SyncAll 多核归约中复用 S_MTE3/MTE2_S 事件同步会确定性触发设备 507035（异步 sticky），排障成本高",
    "507035 为异步 sticky 错误，可能在非预期 case 上浮现，掩盖真实归因"
  ],
  "slug": "s-mte3-event-mix-syncall-error",
  "summary": "试图复用 group_norm.h 的 S->MTE3 事件同步模式保证聚合 val/idx 可见性，在 KERNEL_TYPE_MIX_AIV_1_0 + 硬 SyncAll() 并发下触发设备 507035（type 3，NPU sync 失败，异步 sticky），build1/build2 两轮 A/B 复现；移除 S_MTE3 后 bisect2 通过，写侧回退 PipeBarrier<PIPE_ALL> 实测已够。",
  "verification": {
    "correctness": [
      "build1/build2 两轮 A/B 复现设备 507035；移除 S_MTE3 后 bisect2 通过（case 13 全量 20/20 passed）"
    ],
    "performance": [
      "无独立性能数据：这是正确性阻塞解除（写侧 PipeBarrier 足够），为 S-B 23.0x 与全量 13.40x 的可验收前提"
    ],
    "rollback_signals": [
      "任何 MIX+SyncAll 多核归约中复用 S_MTE3 事件 -> 立即回退 PipeBarrier 并记录设备错误"
    ]
  }
}
-->

# 性能优化策略：S_MTE3 事件同步在 MIX_AIV_1_0 + 硬 SyncAll 上下文触发设备 507035

单一优化点：试图复用 group_norm.h 的 S->MTE3 事件同步模式保证聚合 val/idx 可见性，在 KERNEL_TYPE_MIX_AIV_1_0 + 硬 SyncAll() 并发下触发设备 507035（type 3，NPU sync 失败，异步 sticky），build1/build2 两轮 A/B 复现；移除 S_MTE3 后 bisect2 通过，写侧回退 PipeBarrier<PIPE_ALL> 实测已够。

## 1. 原理

跨流水事件标志（S_MTE3/MTE2_S）与 MIX+硬 SyncAll 的线程级跨核归并组合不兼容；同一模式在纯 AIV 或无线程级跨核归并场景可用（如 group_norm.h），不可直接照搬到需要硬 SyncAll 的多核归约。

实现机制：S_MTE3 SetFlag/WaitFlag 试图把标量写与 MTE3 读排序；在 KERNEL_TYPE_MIX_AIV_1_0 + SyncAll() 下触发设备 507035（NPU sync 失败，异步 sticky）。build1/build2 二分证实为 S_MTE3 所致；移除后 bisect2 通过。写侧回退 PipeBarrier<PIPE_ALL>，读侧（MTE2_S）同疑保留 PipeBarrier。

## 2. 性能问题模式

- 优化目标：保证两阶段跨核扫描中 Pass2 能读到 Pass1 写出的聚合 val/idx（避免用全局 PipeBarrier 的粗粒度同步）。
- 适用数据流：跨核归约中 Scalar->MTE3 事件同步（S_MTE3 SetFlag/WaitFlag）与 KERNEL_TYPE_MIX_AIV_1_0 + 硬 SyncAll() 组合，用于保证聚合 val/idx 的跨核可见性
- Feature signature：`{"bottleneck": ["cross-core-visibility", "sync-primitive-selection"], "error": ["507035-npu-sync-failure"], "pattern": "s-mte3-event-incompatible-with-mix-syncall", "structure": ["scalar-to-mte3-event", "mix-aiv-task", "hard-syncall", "cross-core-aggregate"]}`

## 3. 正确性红线

- 在 MIX+硬 SyncAll 多核归约中复用 S_MTE3/MTE2_S 事件同步会确定性触发设备 507035（异步 sticky），排障成本高
- 507035 为异步 sticky 错误，可能在非预期 case 上浮现，掩盖真实归因

资源与硬件约束：

- 分离模式（MIX_AIV_1_0）多核归约的聚合写->读可见性用 PipeBarrier<PIPE_ALL>，勿用 S_MTE3 事件
- 读侧（MTE2_S）同步同疑，保留 PipeBarrier
- 用 A/B 二分（build1/build2）确认 507035 归因，不要直接改同步方案

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- 两阶段跨核归约需保证聚合 val/idx 的跨核可见性（Pass1 写 -> Pass2 读）
- kernel 采用 KERNEL_TYPE_MIX_AIV_1_0 且两阶段间使用 SyncAll() 硬同步

不适用：

- 纯 AIV 或无线程级跨核归并场景可继续用 S_MTE3（group_norm.h 同模式实测可用）

## 5. 实施步骤

1. 识别跨核归约聚合写->读可见性需求，评估同步原语选型
2. 勿在 MIX_AIV_1_0 + 硬 SyncAll 上下文使用 S_MTE3/MTE2_S 事件同步
3. 写侧用 PipeBarrier<PIPE_ALL> 排序，读侧保留 PipeBarrier
4. 用 A/B 二分（build1/build2）确认 507035 归因后再定稿同步方案

## 6. LLM 前置问题

- 目标实现是否满足：两阶段跨核归约需保证聚合 val/idx 的跨核可见性（Pass1 写 -> Pass2 读）？
- 目标实现是否满足：kernel 采用 KERNEL_TYPE_MIX_AIV_1_0 且两阶段间使用 SyncAll() 硬同步？
- 是否命中排除条件：纯 AIV 或无线程级跨核归并场景可继续用 S_MTE3（group_norm.h 同模式实测可用）？

## 7. 验收标准

正确性：

- build1/build2 两轮 A/B 复现设备 507035；移除 S_MTE3 后 bisect2 通过（case 13 全量 20/20 passed）

性能：

- 无独立性能数据：这是正确性阻塞解除（写侧 PipeBarrier 足够），为 S-B 23.0x 与全量 13.40x 的可验收前提

回滚信号：

- 任何 MIX+SyncAll 多核归约中复用 S_MTE3 事件 -> 立即回退 PipeBarrier 并记录设备错误

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260821（status=rejected, case=13）

## 检索卡（短卡）

动作：在MIX_AIV_1_0加硬SyncAll归并中禁用该事件组合，并以可证明的同步保持聚合写到读可见性。
适用：两阶段跨核归约需保证Pass1聚合val/idx写入对Pass2可见。
限制：S_MTE3/MTE2_S事件不得与MIX_AIV_1_0硬SyncAll跨核归并组合。
范围：scan-reduce两阶段MIX多核扫描归约同步路径。
检索词：S_MTE3、MTE2_S、MIX_AIV_1_0、硬SyncAll、Pass1写至Pass2读。
机会：Pass1聚合写到Pass2读之间存在跨核可见性需求，且当前混用事件与硬SyncAll。
