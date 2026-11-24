---
type: Optimization
title: T4 1-D 段归约：GM-direct SIMT 直散射 fp32 原子累加进 per-core workspace
description: 把逐元素 s-pipe RMW 标量链改为 SIMT grid-stride 经 __gm__ 直读并 asc_atomic_add 进每核私有 fp32 workspace。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/t4-simt-gm-direct-atomic-fp32-ws.md
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
      "SIMT __gm__ 读+原子须经 bisection 验证",
      "可见性纪律（asc_threadfence + PipeBarrier<PIPE_ALL> + SyncAll 后 stage2 才可 MTE 读）",
      "避免跨核 GM 写（507034 deadlock 类）；per-core 私有切片意味着无跨核写",
      "fp32 原子顺序 vs golden j-ascending 可能在大有限和上改变舍入（7/7 阈值保护）"
    ],
    "excluded_conditions": [
      "featureLen>1",
      "非 fp32 累加",
      "numSegments==1（保留 T4-allreduce 快路径）",
      "SIMT 读 MTE2-copied int32 ids 或 V-pipe 输出（已证 507035 crash 模式）",
      "fp16/bf16 直接 GM 原子进 y（必须 fp32 累加）"
    ],
    "required_conditions": [
      "featureLen==1（1-D segment sum）",
      "fp32 累加模式",
      "numSegments>1 且 N/numSegments>=5（每核行数足够摊薄）",
      "SIMT 可经 __gm__ 读 ids/data 而不触发 UB-read crash",
      "冻结 T4 workspace 已提供每核 fp32 切片 == S"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "operator_class": "scatter-update",
      "precision": "7/7 PASS",
      "round": 4,
      "run_id": "<run-id>",
      "speedup": "incremental 1.8009x; case12 5.14x, case16 10.40x (official); cumulative 1.8078",
      "status": "accepted"
    },
    {
      "comparison_sha256": "f13cff38845f9a5dd3559a9634d4a509ec357c31501ebb9c6e05215cb854059c",
      "decision_sha256": "f89b0cd8f23148f41c26e186f80aa2b09262da9811654cabe9aa5fa026e3ec61",
      "operator_class": "scatter-update",
      "performance_sha256": "844bbd1aab682cc49a4e75a7a48c2ef24d397f36987491dc5cce0fe230b0526a",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "f800fae3d65b8648110c78b029f6b0435995a13e43bdff349f9b63ffd5759a7c",
      "verify_sha256": "1dd18d958012cf7ba9ae078aaa211548247980f3c23ca84494c6022c58b67f46"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-dependency-chain",
      "s-pipe-serialization"
    ],
    "dtypes": [
      "fp32"
    ],
    "pattern": "simt-gm-direct-atomic",
    "structure": [
      "simt-grid-stride",
      "gm-atomic-add",
      "per-core-workspace",
      "cross-core-vector-reduce"
    ]
  },
  "generality": "op_class",
  "id": "T4-SIMT-GM-ATOMIC-FP32-WS",
  "implementation_steps": [
    "新建 UnsortedSegmentSumT2NSimtGmAtomic，stage0 清零 per-core ws 切片",
    "stage1 asc_vf_call SIMT grid-stride __gm__ 读 + SimtToFloat + asc_atomic_add",
    "asc_dcci_entire + asc_threadfence + PipeBarrier<PIPE_ALL> + SyncAll 可见性纪律",
    "stage2 复用 T4 跨核向量归约 + 单次 RNE 回写 y",
    "运行时门控 featureLen==1 && fp32-acc && numSegments>1 && N/seg>=5"
  ],
  "intent": "消除 s-pipe 标量依赖链（segAcc[sid]+=data[jj] 同址 GetValue/SetValue L0 延迟串行化），其使两个 R5 case 达 96-97% aiv_scalar bound。",
  "mechanism": "UnsortedSegmentSumT2NSimtGmAtomic：stage0 清零每核私有 fp32 ws 切片；stage1 asc_vf_call<UssGmScatterAtomicFp32> SIMT grid-stride 读 segmentIdsGm_/dataGm_（__gm__），SimtToFloat，asc_atomic_add(&wsPartialGm_[sid], f)（asc_dcci_entire 前置防 stale cache），asc_threadfence + PipeBarrier<PIPE_ALL> + SyncAll；stage2 复用 T4 跨核向量归约 + 单次 RNE 回写 y。运行时门控 featureLen==1 && isFp32Acc && numSegments>1 && N/numSegments>=5。",
  "name": "T4 1-D 段归约：GM-direct SIMT 直散射 fp32 原子累加进 per-core workspace",
  "operator_class": "scatter-update",
  "operator_scope": "1-D segment-sum 归约数据流（featureLen==1, fp32 累加, 每核可私有输出切片）",
  "principle": "当每个更新映射到 GM 地址且可建立每核输出切片所有权时，SIMT grid 可直接对 GM 发 scatter-add（并行发射、仅同址冲突硬件串行），替代长标量依赖链；fp32 中间累加 + 单次回写匹配 golden 精度。",
  "related_anti_patterns": [],
  "risks": [
    "SIMT stale-cache 或可见性缺失导致更新静默丢失",
    "跨核原子竞争或死锁（507034）",
    "大有限和 fp32 舍入顺序差异"
  ],
  "slug": "t4-simt-gm-direct-atomic-fp32-ws",
  "summary": "对 R5 1-D 段归约 route（featureLen==1, fp32 累加）的 SCALAR_BOUND 逐元素 s-pipe RMW 链，改为 kernel 侧 SIMT 路径：per-core SIMT 线程经 __gm__ 指针直接读 segmentIds/data，拓宽为 fp32（SimtToFloat），asc_atomic_add 进每核私有 fp32 workspace 切片（零跨核原子竞争），再 PipeBarrier+SyncAll 复用 T4 跨核向量归约 + 单次回写 y。纯 kernel 改动，复用冻结 host TilingData。",
  "verification": {
    "correctness": [
      "7/7 validation cases passed；bisection (a)(b)(c) 全 no-crash"
    ],
    "performance": [
      "incremental_total_speedup=1.8009；case12/16 5.14x/10.40x（官方路径 case16 10.40x）；cumulative 1.8078；aiv_scalar 0.959->0.025 / 0.974->0.030"
    ],
    "rollback_signals": [
      "SIMT crash（507035/507034）、case12/16 aiv_scalar 未降、官方 elapsed 未改善时回退"
    ]
  }
}
-->

# 性能优化策略：T4 1-D 段归约：GM-direct SIMT 直散射 fp32 原子累加进 per-core workspace

单一优化点：对 R5 1-D 段归约 route（featureLen==1, fp32 累加）的 SCALAR_BOUND 逐元素 s-pipe RMW 链，改为 kernel 侧 SIMT 路径：per-core SIMT 线程经 __gm__ 指针直接读 segmentIds/data，拓宽为 fp32（SimtToFloat），asc_atomic_add 进每核私有 fp32 workspace 切片（零跨核原子竞争），再 PipeBarrier+SyncAll 复用 T4 跨核向量归约 + 单次回写 y。纯 kernel 改动，复用冻结 host TilingData。

## 1. 原理

当每个更新映射到 GM 地址且可建立每核输出切片所有权时，SIMT grid 可直接对 GM 发 scatter-add（并行发射、仅同址冲突硬件串行），替代长标量依赖链；fp32 中间累加 + 单次回写匹配 golden 精度。

实现机制：UnsortedSegmentSumT2NSimtGmAtomic：stage0 清零每核私有 fp32 ws 切片；stage1 asc_vf_call<UssGmScatterAtomicFp32> SIMT grid-stride 读 segmentIdsGm_/dataGm_（__gm__），SimtToFloat，asc_atomic_add(&wsPartialGm_[sid], f)（asc_dcci_entire 前置防 stale cache），asc_threadfence + PipeBarrier<PIPE_ALL> + SyncAll；stage2 复用 T4 跨核向量归约 + 单次 RNE 回写 y。运行时门控 featureLen==1 && isFp32Acc && numSegments>1 && N/numSegments>=5。

## 2. 性能问题模式

- 优化目标：消除 s-pipe 标量依赖链（segAcc[sid]+=data[jj] 同址 GetValue/SetValue L0 延迟串行化），其使两个 R5 case 达 96-97% aiv_scalar bound。
- 适用数据流：1-D segment-sum 归约数据流（featureLen==1, fp32 累加, 每核可私有输出切片）
- Feature signature：`{"bottleneck": ["scalar-dependency-chain", "s-pipe-serialization"], "dtypes": ["fp32"], "pattern": "simt-gm-direct-atomic", "structure": ["simt-grid-stride", "gm-atomic-add", "per-core-workspace", "cross-core-vector-reduce"]}`

## 3. 正确性红线

- SIMT stale-cache 或可见性缺失导致更新静默丢失
- 跨核原子竞争或死锁（507034）
- 大有限和 fp32 舍入顺序差异

资源与硬件约束：

- SIMT __gm__ 读+原子须经 bisection 验证
- 可见性纪律（asc_threadfence + PipeBarrier<PIPE_ALL> + SyncAll 后 stage2 才可 MTE 读）
- 避免跨核 GM 写（507034 deadlock 类）；per-core 私有切片意味着无跨核写
- fp32 原子顺序 vs golden j-ascending 可能在大有限和上改变舍入（7/7 阈值保护）

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- featureLen==1（1-D segment sum）
- fp32 累加模式
- numSegments>1 且 N/numSegments>=5（每核行数足够摊薄）
- SIMT 可经 __gm__ 读 ids/data 而不触发 UB-read crash
- 冻结 T4 workspace 已提供每核 fp32 切片 == S

不适用：

- featureLen>1
- 非 fp32 累加
- numSegments==1（保留 T4-allreduce 快路径）
- SIMT 读 MTE2-copied int32 ids 或 V-pipe 输出（已证 507035 crash 模式）
- fp16/bf16 直接 GM 原子进 y（必须 fp32 累加）

## 5. 实施步骤

1. 新建 UnsortedSegmentSumT2NSimtGmAtomic，stage0 清零 per-core ws 切片
2. stage1 asc_vf_call SIMT grid-stride __gm__ 读 + SimtToFloat + asc_atomic_add
3. asc_dcci_entire + asc_threadfence + PipeBarrier<PIPE_ALL> + SyncAll 可见性纪律
4. stage2 复用 T4 跨核向量归约 + 单次 RNE 回写 y
5. 运行时门控 featureLen==1 && fp32-acc && numSegments>1 && N/seg>=5

## 6. LLM 前置问题

- 目标实现是否满足：featureLen==1（1-D segment sum）？
- 目标实现是否满足：fp32 累加模式？
- 目标实现是否满足：numSegments>1 且 N/numSegments>=5（每核行数足够摊薄）？
- 是否命中排除条件：featureLen>1？

## 7. 验收标准

正确性：

- 7/7 validation cases passed；bisection (a)(b)(c) 全 no-crash

性能：

- incremental_total_speedup=1.8009；case12/16 5.14x/10.40x（官方路径 case16 10.40x）；cumulative 1.8078；aiv_scalar 0.959->0.025 / 0.974->0.030

回滚信号：

- SIMT crash（507035/507034）、case12/16 aiv_scalar 未降、官方 elapsed 未改善时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- unsorted_segment_sum-20260830_063304-215ec0（round=4, status=accepted, speedup=incremental 1.8009x; case12 5.14x, case16 10.40x (official); cumulative 1.8078）
- unsorted_segment_sum-20260830_063304-215ec0（round=4, status=accepted）

## 检索卡（短卡）

动作：把逐元素 s-pipe RMW 标量链改为 SIMT grid-stride 经 __gm__ 直读并 asc_atomic_add 进每核私有 fp32 workspace。
适用：featureLen==1；fp32 累加；numSegments>1 且 N/numSegments>=5。
限制：禁跨核 GM 写（507034 deadlock）；SIMT 读 MTE2-copied int32 ids 会 507035 crash。
范围：1-D segment-sum 归约的累加相位
检索词：asc_vf_call、__gm__、asc_atomic_add、asc_dcci_entire、threadfence
机会：segAcc[sid]+=data[jj] 同址 SetValue/GetValue 串行化，aiv_scalar 96-97%
代价：fp32 原子顺序异于 golden，大有限和舍入可能改变
