---
type: Optimization
title: "X113: MIX 单 kernel 把 epilogue 藏进 cube 的 MTE2 阴影（整 slab 生产者-消费者 + 全 N 单次 IterateAll）"
description: "把 cube 段（受 L2→L1 回填限制）与向量后处理合成一个 MIX 单 kernel，让 epilogue 藏进 cube 的搬运阴影；适用于两段串行且 cube 段本身受回填限制的算子。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/pipeline_scheduling.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/CrossCoreSetFlag_ISASI.md
    role: constraint
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x113.json
    role: evidence
created_at: "2026-10-26T00:00:00Z"
updated_at: "2026-10-26T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X113）。
>
> 原始元数据：
>
> ```yaml
> id: X113
> origin: discovered
> confidence: single_op
> op_families: [matmul, moe, quantization, cv-mix]
> bottlenecks: [no_overlap, mte2_stall, partial_overlap]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x113.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x113.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X113: MIX 单 kernel 把 epilogue 藏进 cube 的 MTE2 阴影（整 slab 生产者-消费者 + 全 N 单次 IterateAll）

## 核心思路
matmul + 向量后处理的两段 kernel 是**串行**的：cube 段 2590us + epilogue 段 455us = 3045us。
但 cube 段本身是 MTE2（L2→L1 回填）bound、AIV 侧在整段时间里几乎空闲。把两段合成
**一个 MIX_AIC_1_2 kernel**：AIC 按「整 slab」产出 C 平面并置跨核 flag，AIV 的 (2i,2i+1) 对等
flag 后就地做 epilogue —— epilogue 的向量时间被完全藏进 cube 的搬运阴影，只多付它的
C 面 L2 流量（0.34GB ≈ 109us）。

## 实现要点
- **必须单独成一个 TU**（`KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_MIX_AIC_1_2)` 写在函数体首行）；
 与其它 kernel 同 TU 会把整个 TU 的 task type 改掉，其它 kernel 静默 no-op（107000 注册失败）。
- **slab = 一个 (expert, m-tile) 的整条输出行块**（96×8192 fp16 = 1.5MB）：
 AIC 把 flat tile list 重组成「一个 slab 的两次 n-half IterateAll 连续做完」再置 flag，
 AIV 侧按 `GetSubBlockIdx()` 拆行，跑与两段式**逐位相同**的 epilogue（同 op 同序）。
- **同步只用单向 flag ring**：`CrossCoreSetFlag<0x2, PIPE_FIX>(id)` → `CrossCoreWaitFlag(id)`，
 消费者按产出顺序消费，flag 只需区分「上一块 / 当前块」。
- **AIV 侧核号**：`MIX_AIC_1_2` 下 `GetBlockNum()` 返回 AIC 数（24）而 `GetBlockIdx()` ∈ [0,48)，
 数据切分必须按 48 显式折算。
- **末刀（oneIter）**：让一个 slab 用**一次覆盖全 N 的 IterateAll** 产出（而非每个 n-half 一次），
 省掉每次 IterateAll 的 A 面板重取与 SetOrgShape —— 单测 -50us。
- 回退：`GMSQ_FUSE=0` 逐字回到两段式 kernel；新路径只在 fastPath 内启用。

## 适用场景
- 前段 kernel 是搬运/cube bound、后段是向量/带宽 bound 的「matmul + 逐元素后处理」融合算子
 （MoE FFN、SwiGLU、per-token quant、RMSNorm 等）。
- 反例：两段都吃满 L2 带宽时融合无收益（见 F13 的早期两次证伪，它们的 epilogue 是 895us 且未解决同步）。

## 验证状态

定量结果（基线/变体、用例数、聚合口径）见证据包；正文只保留机制、判据与边界。

## 约束 / 坑
 反之，两段式下同样的改动值 21us（那时 AIV 就是关键路径）。**融合态要优化 cube，不是 epilogue**。
- 末波（176 slab / 24 核）**不可通过细化粒度或均衡列切分修复**：实测把尾部 slab 换成跨专家切分
 反而 -141us（尾部拉 8 个专家的冷 B ≈ 256MB），列切分均衡 3108 vs 3048 —— 末波是共享 L2 带宽 bound。
- 不可用 GM 完成计数做 publish：AIC 没有 UB，只能 scalar `GlobalTensor::SetValue`，对另一核的
 DMA 不可见（实测 242ms/call）。