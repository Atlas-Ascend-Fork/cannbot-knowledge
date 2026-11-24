---
type: Optimization
title: DMA 原子散射累加
description: 利用 DMA 写回阶段的原子加能力直接更新 GM，去掉显式读取目标值的步骤。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/mte3-atomic-scatter-add.md
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
      "原子模式必须在最小必要作用域内启用，并在所有出口显式关闭，避免污染后续搬运",
      "模板代码必须用编译期分支隔离不支持的 dtype，不能只依赖运行期条件"
    ],
    "excluded_conditions": [
      "非加法归约、顺序敏感更新或不支持原子写回的数据类型不能使用该路径",
      "低精度多次原子累加无法满足误差要求时，应改用高精度工作区累加"
    ],
    "required_conditions": [
      "归约运算为加法，目标 dtype 与目标平台均在 DMA 原子加支持范围内",
      "输出在进入原子更新前已按算子语义初始化为正确的初值",
      "每次写回的地址、长度、对齐和步幅能够由目标 DMA 接口合法表达"
    ]
  },
  "applicability_boundary": "",
  "classification": "validated_strategy",
  "created": "2026-08-21",
  "evidence": [
    {
      "after_us": 56.0,
      "before_us": 765.0,
      "case": "2",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/strategies/unsorted_segment_sum_opt_20260820.md",
      "speedup": 13.6,
      "status": "accepted"
    },
    {
      "after_us": 26.4,
      "before_us": 1543.6,
      "case": "9",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/scatter/<run-id>/winning_diffs/t1t2t4_fp32add_phase2.meta.json",
      "speedup": 58.4,
      "status": "accepted"
    },
    {
      "comparison_sha256": "ece59c66fb05ddeaa6a813d98e79272bf6631d3aff3921c1f812d5406fd4e8ae",
      "decision_sha256": "7480159c0d71231e86ffc34dfa833a2699646e34634c715e18ed52f1be9920e2",
      "operator_class": "scatter-update",
      "performance_sha256": "5eeb347f08a3781e5602522f7492fbd67d83e37bfa539c3b5ade9dfba13570c7",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "1f832f523f4f8cec4b5c7ce4877dd13e7463b18b8b400b7978e5bdaed8449ed9",
      "verify_sha256": "a86b61a761bf2d091ab5884c4bfcebd8c6bc00479e4d62b8616dc6349714c0ac"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "gm-rmw"
    ],
    "dtypes": [
      "int32",
      "fp32",
      "fp16",
      "bf16"
    ],
    "pattern": "mte3-atomic-scatter-add",
    "reduce_mode": "add",
    "structure": [
      "atomic",
      "scatter",
      "mte3"
    ]
  },
  "gain": "UnsortedSegmentSum fp32/int32 用例 13.6–16.3x；Scatter fp32-add case_9 1543.6→26.4us（58.4x）。",
  "generality": "op_class",
  "id": "S2",
  "implementation_steps": [
    "确认输出初值契约、重复地址语义和目标平台的原子写回类型白名单",
    "将更新值按 tile 搬入并完成必要计算，不再读取目标 GM 的旧值",
    "在写回前启用原子加模式，以合法的块参数把 tile 直接累加到目标地址",
    "写回完成后关闭原子模式，并在 buffer 复用前等待写回流水完成",
    "为不支持类型、精度不足和非加法归约保留非原子回退路径"
  ],
  "instance_ids": [
    "S2-GmMulCAS"
  ],
  "intent": "替代逐行 GM RMW 的原子散射",
  "mechanism": "MTE3 原子散射累加：SetAtomicAdd<T>() 逐 tile 包裹逐行 DataCopyPad → DisableDmaAtomic()。消除 y 读（流量减半）与逐行事件；同步降为每 tile 一次 MTE3_MTE2 排空。前置契约：y 预置 0。硬约束：SetAtomicAdd 白名单无 int64，模板类必须 if constexpr 消隐。",
  "name": "DMA 原子散射累加",
  "op": "seed",
  "operator_class": "scatter-update",
  "operator_scope": "支持 DMA 原子加数据类型、目标地址可由规则块搬运描述的散射加或分段累加路径",
  "principle": "普通 read-modify-write 需要读取旧值、片上计算再写回；若写回引擎能够执行原子加，可将旧值读取和对应同步从热循环中移除，并由硬件串行化同址更新。",
  "provenance": {
    "skill": "SKILL.md §7 S2"
  },
  "related_anti_patterns": [
    "per-row-gm-rmw"
  ],
  "related_seed_ids": [],
  "risks": [
    "原子状态泄漏会让后续普通 DataCopy 意外变为累加写，造成难以定位的静默错误",
    "热点地址冲突会降低原子吞吐，低精度累加顺序还可能放大舍入误差"
  ],
  "schema_version": 2,
  "slug": "mte3-atomic-scatter-add",
  "source": "skill",
  "status": "applied",
  "summary": "利用 DMA 写回阶段的原子加能力直接更新 GM，去掉显式读取目标值的步骤。",
  "verification": {
    "correctness": [
      "覆盖唯一索引、重复索引、热点冲突、尾块和所有支持 dtype，并检查原子模式退出后普通搬运语义",
      "验证输出初始化、空更新和多核并发下的累加结果"
    ],
    "performance": [
      "确认目标值 GM 读取消失、写回描述符与同步次数下降，并分别测量低冲突和高冲突分布"
    ],
    "rollback_signals": [
      "出现类型编译失败、原子状态泄漏、低精度误差超限或高冲突吞吐恶化时回退"
    ]
  }
}
-->

# 性能优化策略：DMA 原子散射累加

单一优化点：利用 DMA 写回阶段的原子加能力直接更新 GM，去掉显式读取目标值的步骤。

## 1. 原理

普通 read-modify-write 需要读取旧值、片上计算再写回；若写回引擎能够执行原子加，可将旧值读取和对应同步从热循环中移除，并由硬件串行化同址更新。

实现机制：MTE3 原子散射累加：SetAtomicAdd<T>() 逐 tile 包裹逐行 DataCopyPad → DisableDmaAtomic()。消除 y 读（流量减半）与逐行事件；同步降为每 tile 一次 MTE3_MTE2 排空。前置契约：y 预置 0。硬约束：SetAtomicAdd 白名单无 int64，模板类必须 if constexpr 消隐。

## 2. 性能问题模式

- 优化目标：替代逐行 GM RMW 的原子散射
- 适用数据流：支持 DMA 原子加数据类型、目标地址可由规则块搬运描述的散射加或分段累加路径
- Feature signature：`{"bottleneck": ["gm-rmw"], "dtypes": ["int32", "fp32", "fp16", "bf16"], "pattern": "mte3-atomic-scatter-add", "reduce_mode": "add", "structure": ["atomic", "scatter", "mte3"]}`

## 3. 正确性红线

- 原子状态泄漏会让后续普通 DataCopy 意外变为累加写，造成难以定位的静默错误
- 热点地址冲突会降低原子吞吐，低精度累加顺序还可能放大舍入误差

资源与硬件约束：

- 原子模式必须在最小必要作用域内启用，并在所有出口显式关闭，避免污染后续搬运
- 模板代码必须用编译期分支隔离不支持的 dtype，不能只依赖运行期条件

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- 归约运算为加法，目标 dtype 与目标平台均在 DMA 原子加支持范围内
- 输出在进入原子更新前已按算子语义初始化为正确的初值
- 每次写回的地址、长度、对齐和步幅能够由目标 DMA 接口合法表达

不适用：

- 非加法归约、顺序敏感更新或不支持原子写回的数据类型不能使用该路径
- 低精度多次原子累加无法满足误差要求时，应改用高精度工作区累加

## 5. 实施步骤

1. 确认输出初值契约、重复地址语义和目标平台的原子写回类型白名单
2. 将更新值按 tile 搬入并完成必要计算，不再读取目标 GM 的旧值
3. 在写回前启用原子加模式，以合法的块参数把 tile 直接累加到目标地址
4. 写回完成后关闭原子模式，并在 buffer 复用前等待写回流水完成
5. 为不支持类型、精度不足和非加法归约保留非原子回退路径

## 6. LLM 前置问题

- 目标实现是否满足：归约运算为加法，目标 dtype 与目标平台均在 DMA 原子加支持范围内？
- 目标实现是否满足：输出在进入原子更新前已按算子语义初始化为正确的初值？
- 目标实现是否满足：每次写回的地址、长度、对齐和步幅能够由目标 DMA 接口合法表达？
- 是否命中排除条件：非加法归约、顺序敏感更新或不支持原子写回的数据类型不能使用该路径？

## 7. 验收标准

正确性：

- 覆盖唯一索引、重复索引、热点冲突、尾块和所有支持 dtype，并检查原子模式退出后普通搬运语义
- 验证输出初始化、空更新和多核并发下的累加结果

性能：

- 确认目标值 GM 读取消失、写回描述符与同步次数下降，并分别测量低冲突和高冲突分布

回滚信号：

- 出现类型编译失败、原子状态泄漏、低精度误差超限或高冲突吞吐恶化时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-gm-rmw

- strategy-unsorted-segment-sum-20260820-uss-002（status=accepted, case=2, speedup=13.6）
- ksearch-scatter-20260814-fp32-add（status=accepted, case=9, speedup=58.4）
- scatter-<run-id>（round=1, status=accepted）

## 检索卡（短卡）

动作：用MTE3写回原子加替代逐行GM读改写，从热循环移除旧值读取与同步，由硬件串行化同址更新
适用：归约为加法，dtype与平台支持DMA原子加，输出已按语义初始化
限制：原子模式仅在最小作用域启用且所有出口显式关闭；须确认初值、重复地址语义和类型白名单
范围：scatter-reduce的散射加或分段累加写回路径
检索词：MTE3、DMA原子加、SetAtomicAdd、DataCopy、GM RMW
机会：逐行GM RMW，且散射或分段累加地址可由规则块搬运描述
代价：热点地址冲突会降低原子吞吐
