---
type: Optimization
title: 跨流水同步的批级摊销
description: 把逐元素或逐行同步提升到批次边界，在批内集中生产、消费和写回。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/batched-sync-amortization.md
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
      "批大小必须由 UB 容量、队列深度、事件槽位和单次 API 上限共同计算",
      "所有跨流水依赖都要在批级数据流图中重新证明，不能直接删除原同步"
    ],
    "excluded_conditions": [
      "工作单元间存在严格生产消费链、顺序敏感副作用或逐项同步是可见性契约时不适用",
      "单个工作单元已占满 UB、批大小只能为一时没有摊销空间"
    ],
    "required_conditions": [
      "批内工作单元不存在必须逐项提交的依赖，可以先集中搬入再集中计算或写回",
      "UB 能同时容纳批内活动数据及必要的环形槽位",
      "批内若更新同一地址，能够证明顺序无关或完成地址去重"
    ]
  },
  "applicability_boundary": "",
  "classification": "validated_strategy",
  "created": "2026-08-21",
  "evidence": [
    {
      "after_us": 1165.0,
      "before_us": 4383.0,
      "case": "5",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/unsorted_segment_sum_opt_20260820.md",
      "speedup": 3.8,
      "status": "accepted"
    },
    {
      "after_us": 16.863,
      "before_us": 44.24,
      "case": "baseline-anchor",
      "operator_class": "normalization",
      "precision": "ALL PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/rms_norm/<run-id>/phase6_apply/final_report.md",
      "speedup": 2.62,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "row-sync",
      "barrier-amortization"
    ],
    "dtypes": [],
    "pattern": "batched-sync",
    "reduce_mode": "row-reduce",
    "structure": [
      "batching",
      "sync-amortization"
    ]
  },
  "gain": "Scatter-reduce 逐行事件批化 case_5 3.8x；Normalization 多行队列批化锚点 2.62x。",
  "generality": "common",
  "id": "S3",
  "implementation_steps": [
    "画出单个工作单元的流水依赖图，标出每个 SetFlag/WaitFlag 或 barrier 保护的数据",
    "选择可独立组合的批次边界，并按 UB 与队列容量计算动态批大小",
    "将批内搬入集中发射，等待一次后连续执行计算，再以同样方式集中写回",
    "需要多槽复用时使用环形索引，并在覆盖槽位前等待最后一个消费者完成",
    "单独处理尾批，批大小为一时保持与原路径等价"
  ],
  "instance_ids": [],
  "intent": "消除逐行同步循环的流水排空",
  "mechanism": "按 UB、队列深度和事件槽位动态选择批大小；批内集中发射 MTE2，完成一次 MTE2_V 同步后连续计算，再经一次 V_MTE3 同步集中写回。多批之间用环形槽位复用缓冲，覆盖槽位前等待最后一个消费者完成；批内同址更新必须证明顺序无关或先完成地址去重。",
  "name": "跨流水同步的批级摊销",
  "op": "seed",
  "operator_class": "",
  "operator_scope": "循环内反复执行 MTE2、V、S、MTE3 等跨流水同步，且相邻迭代彼此独立的数据流",
  "principle": "事件设置、等待和流水排空具有与数据量无关的固定成本；把多个独立工作单元组成批次，可以让一次同步覆盖多个单元，同时为不同流水提供更长的连续工作区间。",
  "provenance": {
    "skill": "SKILL.md §7 S3"
  },
  "related_anti_patterns": [
    "per-row-pipebarrier-sync"
  ],
  "related_seed_ids": [],
  "risks": [
    "过度后移同步会读取未就绪数据，过早复用槽位会覆盖仍在消费的数据",
    "批大小过大会增加 UB 压力和尾部浪费，反而降低并行度"
  ],
  "schema_version": 2,
  "slug": "batched-sync-amortization",
  "source": "skill",
  "status": "applied",
  "summary": "把逐元素或逐行同步提升到批次边界，在批内集中生产、消费和写回。",
  "verification": {
    "correctness": [
      "覆盖满批、尾批、批大小为一、槽位回绕和同址更新场景，并检查跨流水可见性"
    ],
    "performance": [
      "用 profile 确认同步次数从逐工作单元下降到逐批次，同时观察各流水空闲比例和 UB 占用"
    ],
    "rollback_signals": [
      "出现偶发错误、事件死锁、槽位覆盖、UB 超限或批化后流水空洞增大时回退"
    ]
  }
}
-->

# 性能优化策略：跨流水同步的批级摊销

单一优化点：把逐元素或逐行同步提升到批次边界，在批内集中生产、消费和写回。

## 1. 原理

事件设置、等待和流水排空具有与数据量无关的固定成本；把多个独立工作单元组成批次，可以让一次同步覆盖多个单元，同时为不同流水提供更长的连续工作区间。

实现机制：按 UB、队列深度和事件槽位动态选择批大小；批内集中发射 MTE2，完成一次 MTE2_V 同步后连续计算，再经一次 V_MTE3 同步集中写回。多批之间用环形槽位复用缓冲，覆盖槽位前等待最后一个消费者完成；批内同址更新必须证明顺序无关或先完成地址去重。

## 2. 性能问题模式

- 优化目标：消除逐行同步循环的流水排空
- 适用数据流：循环内反复执行 MTE2、V、S、MTE3 等跨流水同步，且相邻迭代彼此独立的数据流
- Feature signature：`{"bottleneck": ["row-sync", "barrier-amortization"], "dtypes": [], "pattern": "batched-sync", "reduce_mode": "row-reduce", "structure": ["batching", "sync-amortization"]}`

## 3. 正确性红线

- 过度后移同步会读取未就绪数据，过早复用槽位会覆盖仍在消费的数据
- 批大小过大会增加 UB 压力和尾部浪费，反而降低并行度

资源与硬件约束：

- 批大小必须由 UB 容量、队列深度、事件槽位和单次 API 上限共同计算
- 所有跨流水依赖都要在批级数据流图中重新证明，不能直接删除原同步

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 批内工作单元不存在必须逐项提交的依赖，可以先集中搬入再集中计算或写回
- UB 能同时容纳批内活动数据及必要的环形槽位
- 批内若更新同一地址，能够证明顺序无关或完成地址去重

不适用：

- 工作单元间存在严格生产消费链、顺序敏感副作用或逐项同步是可见性契约时不适用
- 单个工作单元已占满 UB、批大小只能为一时没有摊销空间

## 5. 实施步骤

1. 画出单个工作单元的流水依赖图，标出每个 SetFlag/WaitFlag 或 barrier 保护的数据
2. 选择可独立组合的批次边界，并按 UB 与队列容量计算动态批大小
3. 将批内搬入集中发射，等待一次后连续执行计算，再以同样方式集中写回
4. 需要多槽复用时使用环形索引，并在覆盖槽位前等待最后一个消费者完成
5. 单独处理尾批，批大小为一时保持与原路径等价

## 6. LLM 前置问题

- 目标实现是否满足：批内工作单元不存在必须逐项提交的依赖，可以先集中搬入再集中计算或写回？
- 目标实现是否满足：UB 能同时容纳批内活动数据及必要的环形槽位？
- 目标实现是否满足：批内若更新同一地址，能够证明顺序无关或完成地址去重？
- 是否命中排除条件：工作单元间存在严格生产消费链、顺序敏感副作用或逐项同步是可见性契约时不适用？

## 7. 验收标准

正确性：

- 覆盖满批、尾批、批大小为一、槽位回绕和同址更新场景，并检查跨流水可见性

性能：

- 用 profile 确认同步次数从逐工作单元下降到逐批次，同时观察各流水空闲比例和 UB 占用

回滚信号：

- 出现偶发错误、事件死锁、槽位覆盖、UB 超限或批化后流水空洞增大时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related anti-patterns：per-row-pipebarrier-sync

- strategy-unsorted-segment-sum-20260820-uss-004（status=accepted, case=5, speedup=3.8）
- ksearch-rms-norm-<run-id>（status=accepted, case=baseline-anchor, speedup=2.62）

## 检索卡（短卡）

动作：将逐单元跨流水同步改为独立单元批处理，使一次同步覆盖多个单元。
适用：批内单元相互独立、无需逐项提交，且UB可容纳活动数据和必要环形槽位。
限制：批大小须受UB、队列深度、事件槽位及单次API上限共同约束；不得读取未就绪数据或提前复用槽位。
范围：跨算子类别的多流水独立工作单元循环。
检索词：批级摊销、SetFlag、WaitFlag、MTE2、V、S、MTE3、事件槽位
机会：循环反复进行MTE2、V、S、MTE3同步，且相邻迭代独立。
代价：批过大会增加UB压力和尾部浪费。
