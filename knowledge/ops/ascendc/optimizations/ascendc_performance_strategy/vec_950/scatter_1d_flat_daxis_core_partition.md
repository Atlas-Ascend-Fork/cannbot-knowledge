---
type: Optimization
title: 退化 1D flat update 的 D 轴核心划分
description: 对退化的 1D flat update（scTotal=1 只激活 core 0）增加 D 轴核心划分：每个核拷贝并散射落在其连续 D 切片内的更新，把单核 copy+scatter 摊到全核。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/scatter-1d-flat-daxis-core-partition.md
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
      "gate 必须严格 reduceMode==0 && innerLen==1 && scTotal<blockDim，避免波及其它 update 路由",
      "dimSize 不可整除 blockDim 时 D 切片边界必须正确处理（尾核只到 dimSize）",
      "新增 VF 必须独立于既有 ScatterGmSimtUpdate/ScatterGmSimt，使其它分支字节不变"
    ],
    "excluded_conditions": [
      "reduceMode!=0 或 innerLen>1 的常规列切片路径不适用（保持原实现）",
      "scTotal>=blockDim 时列切片已足够并行，D 轴划分无收益"
    ],
    "required_conditions": [
      "GM-direct update 模式（reduceMode==0），形状退化为 outerLen==innerLen==1 且 scTotal<blockDim",
      "update 是纯存储 y[d]=u（无 RMW/原子/重排），且索引互斥保证每个 d 只被一个核命中",
      "目标平台支持核间 D 切片互斥写入（无跨核写、无 SyncAll 依赖）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "37765867ee8f51c29d8bfa079e8b50013ba972c814f5ed18d0340b2cf7708355",
      "decision_sha256": "6a89fe3a5513af0764ef026eb518b9e9a587dc7fdb7c86c134e968803b8f4c7e",
      "operator_class": "scatter-update",
      "performance_sha256": "1dcd91975dde5819cc80ce23e16a7b7ceeb7ae8cc8185a87767d8d3c07e7bbd6",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "191d7b87122b067ba680a14c267e269fe812e7f15b27a253fc88278edb04fdca",
      "verify_sha256": "3d843b87ebd6d1bfd0dbbfa786da51c34230f897c3bf537d50049b0412adb37f"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "scalar-address-remap"
    ],
    "dtypes": [
      "fp32"
    ],
    "pattern": "scatter-1d-flat-daxis-core-partition",
    "reduce_mode": "update",
    "structure": [
      "direct-gm",
      "d-axis-partition",
      "mte3-copy"
    ]
  },
  "generality": "op_class",
  "id": "SCATTER-1D-FLAT-DAXIS-CORE-PARTITION",
  "implementation_steps": [
    "在 Init 的列切片派生前加 D 轴划分分支（gate 见 constraints）并设置 dAxisPartition_ 标志",
    "Process 中当 dAxisPartition_ 时：每核 MTE3 拷贝 data[dStart_..dEnd_)→y（内层 loop 到 COPY_CHUNK_ELEMS）",
    "PipeBarrier<PIPE_ALL> 排空本核 MTE3 拷贝",
    "新增 VF 按 grid-stride 遍历全部 update，仅对 d∈[dStart_,dEnd_) 执行 yGm[d]=updGm[j]",
    "对非整除 dimSize 的边界与 1D 大 shape 做正确性验证"
  ],
  "intent": "消除 GM-direct update 在退化单列形状（1D flat，scTotal=1）下的核心利用率灾难：data→y 拷贝与全部 scatter 只跑在 core 0。",
  "mechanism": "在 ScatterGmKernel::Init 于列切片前增加 gate（reduceMode==0 && innerLen==1 && scTotal<blockDim）的 D 轴划分分支：dStart_=coreId*perCoreD、dEnd_=min(dStart_+perCoreD, dimSize_)。Process 中每个核 MTE3 拷贝自己的 data[dStart_..dEnd_)→y，PipeBarrier<PIPE_ALL> 后再由新 VF ScatterGmSimtUpdateDAxis grid-stride 过滤 idx 落在本核 D 切片的更新执行 y[d]=u。",
  "name": "退化 1D flat update 的 D 轴核心划分",
  "operator_class": "scatter-update",
  "operator_scope": "GM-direct update 模式下 outerLen==innerLen==1（scTotal 退化）导致列切片把全部工作压到单核的 1D flat 散射更新数据流",
  "principle": "列切片分区以 scTotal 为任务数，当 outerLen==innerLen==1 时 scTotal=1 使 64 核只剩 1 核工作；若按输出索引轴 D 连续切片分配，每个核只负责自己的 D 区间（拷贝 + 过滤 scatter），单核延迟可被约 blockDim 倍摊薄，且 D 切片互斥保证无跨核写、无需 SyncAll。",
  "risks": [
    "D 切片重叠或索引互斥被破坏会引入跨核写竞态（本项目以 golden distinct-index 保证规避）",
    "dimSize 极大时 perCoreD 超过单核拷贝吞吐反而受限；需验证摊薄收益超过启动开销"
  ],
  "slug": "scatter-1d-flat-daxis-core-partition",
  "summary": "对退化的 1D flat update（scTotal=1 只激活 core 0）增加 D 轴核心划分：每个核拷贝并散射落在其连续 D 切片内的更新，把单核 copy+scatter 摊到全核。",
  "verification": {
    "correctness": [
      "覆盖 1D flat update、非整除 D 边界、空切片和全部 dtype，确认 D 切片互斥无跨核写"
    ],
    "performance": [
      "测量 core0 单核 elapsed 到多核摊薄后的 elapsed，确认 scalar+mte2 热点消失"
    ],
    "rollback_signals": [
      "D 边界越界、跨核写竞态、非目标 update 路由被误命中或摊薄收益消失时回退"
    ]
  }
}
-->

# 性能优化策略：退化 1D flat update 的 D 轴核心划分

单一优化点：对退化的 1D flat update（scTotal=1 只激活 core 0）增加 D 轴核心划分：每个核拷贝并散射落在其连续 D 切片内的更新，把单核 copy+scatter 摊到全核。

## 1. 原理

列切片分区以 scTotal 为任务数，当 outerLen==innerLen==1 时 scTotal=1 使 64 核只剩 1 核工作；若按输出索引轴 D 连续切片分配，每个核只负责自己的 D 区间（拷贝 + 过滤 scatter），单核延迟可被约 blockDim 倍摊薄，且 D 切片互斥保证无跨核写、无需 SyncAll。

实现机制：在 ScatterGmKernel::Init 于列切片前增加 gate（reduceMode==0 && innerLen==1 && scTotal<blockDim）的 D 轴划分分支：dStart_=coreId*perCoreD、dEnd_=min(dStart_+perCoreD, dimSize_)。Process 中每个核 MTE3 拷贝自己的 data[dStart_..dEnd_)→y，PipeBarrier<PIPE_ALL> 后再由新 VF ScatterGmSimtUpdateDAxis grid-stride 过滤 idx 落在本核 D 切片的更新执行 y[d]=u。

## 2. 性能问题模式

- 优化目标：消除 GM-direct update 在退化单列形状（1D flat，scTotal=1）下的核心利用率灾难：data→y 拷贝与全部 scatter 只跑在 core 0。
- 适用数据流：GM-direct update 模式下 outerLen==innerLen==1（scTotal 退化）导致列切片把全部工作压到单核的 1D flat 散射更新数据流
- Feature signature：`{"bottleneck": ["core-underutilization", "scalar-address-remap"], "dtypes": ["fp32"], "pattern": "scatter-1d-flat-daxis-core-partition", "reduce_mode": "update", "structure": ["direct-gm", "d-axis-partition", "mte3-copy"]}`

## 3. 正确性红线

- D 切片重叠或索引互斥被破坏会引入跨核写竞态（本项目以 golden distinct-index 保证规避）
- dimSize 极大时 perCoreD 超过单核拷贝吞吐反而受限；需验证摊薄收益超过启动开销

资源与硬件约束：

- gate 必须严格 reduceMode==0 && innerLen==1 && scTotal<blockDim，避免波及其它 update 路由
- dimSize 不可整除 blockDim 时 D 切片边界必须正确处理（尾核只到 dimSize）
- 新增 VF 必须独立于既有 ScatterGmSimtUpdate/ScatterGmSimt，使其它分支字节不变

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- GM-direct update 模式（reduceMode==0），形状退化为 outerLen==innerLen==1 且 scTotal<blockDim
- update 是纯存储 y[d]=u（无 RMW/原子/重排），且索引互斥保证每个 d 只被一个核命中
- 目标平台支持核间 D 切片互斥写入（无跨核写、无 SyncAll 依赖）

不适用：

- reduceMode!=0 或 innerLen>1 的常规列切片路径不适用（保持原实现）
- scTotal>=blockDim 时列切片已足够并行，D 轴划分无收益

## 5. 实施步骤

1. 在 Init 的列切片派生前加 D 轴划分分支（gate 见 constraints）并设置 dAxisPartition_ 标志
2. Process 中当 dAxisPartition_ 时：每核 MTE3 拷贝 data[dStart_..dEnd_)→y（内层 loop 到 COPY_CHUNK_ELEMS）
3. PipeBarrier<PIPE_ALL> 排空本核 MTE3 拷贝
4. 新增 VF 按 grid-stride 遍历全部 update，仅对 d∈[dStart_,dEnd_) 执行 yGm[d]=updGm[j]
5. 对非整除 dimSize 的边界与 1D 大 shape 做正确性验证

## 6. LLM 前置问题

- 目标实现是否满足：GM-direct update 模式（reduceMode==0），形状退化为 outerLen==innerLen==1 且 scTotal<blockDim？
- 目标实现是否满足：update 是纯存储 y[d]=u（无 RMW/原子/重排），且索引互斥保证每个 d 只被一个核命中？
- 目标实现是否满足：目标平台支持核间 D 切片互斥写入（无跨核写、无 SyncAll 依赖）？
- 是否命中排除条件：reduceMode!=0 或 innerLen>1 的常规列切片路径不适用（保持原实现）？

## 7. 验收标准

正确性：

- 覆盖 1D flat update、非整除 D 边界、空切片和全部 dtype，确认 D 切片互斥无跨核写

性能：

- 测量 core0 单核 elapsed 到多核摊薄后的 elapsed，确认 scalar+mte2 热点消失

回滚信号：

- D 边界越界、跨核写竞态、非目标 update 路由被误命中或摊薄收益消失时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- scatter-20260831_151225-664ffa（round=3, status=accepted）

## 检索卡（短卡）

动作：对退化 1D flat update 增加 D 轴核心划分：每核 MTE3 拷贝自己 D 区间，新 VF 只散射本核 D 切片内的更新。
适用：update（reduceMode==0）、退化 outerLen==innerLen==1、scTotal<blockDim。
限制：gate 须严格 reduceMode==0 && innerLen==1 && scTotal<blockDim；非整除须处理尾边界。
范围：scatter-update 的 GM-direct 1D flat 散射更新数据流。
检索词：ScatterGmKernel、dAxisPartition_、perCoreD、PIPE_ALL、grid-stride
机会：scTotal=1 使 data→y 拷贝与全部 scatter 压在 core 0。
代价：D 切片重叠或索引互斥破坏会引入跨核写竞态；dimSize 极大时吞吐受限。
