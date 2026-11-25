---
type: Optimization
title: "X121: kick 合并 + level-0 整块发射"
description: "纯 AIV 门控类算子的成本常由 device task 数与向量发射条数支配；合并同相位 launch 并用 level-0 count-mask 整块发射，可同时压低每 task 固定开销与指令数。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetMaskCount.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/overhead_optimization.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x121.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X121）。
>
> 原始元数据：
>
> ```yaml
> id: X121
> origin: discovered
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x121.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x121.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X121: kick 合并 + level-0 整块发射

## 核心思路
纯 AIV 门控类算子的成本常由「device task 数 × 每 task 固定开销（~5-10us）」与「向量指令条数」两项支配，
而不是带宽或算力。两步正交改造：
① 把同相位的分支 launch 合并（9 AIV → 4）并把多次 `at::zeros` 合成一次（kick 13→5），
 合并时必须只保留一个 `TPipe` + 按分支最大值定尺寸的 buffer，各分支顺序跑自己的 task 循环；
② 把所有逐元素/归约 helper 从 level-2 `count` 重载改为 level-0 `mask(元素个数)+repeatTimes(≤255)`，
 单条指令最多覆盖 16320 个 fp32 元素（仅 `cnt>=1024` 时启用，小板保留分块）。

## 适用场景
- 纯 AIV、无 Cube；数据量远小于带宽/算力上限（op_statistic 里各 kernel 的 vec/mte2 比值都 <0.5，无 pipe 饱和）
- kernel 段数 ≥6、每段 task 数接近核数（每核 ~1 task，跨 task 无法预取）
- 典型：cv-attn 门控家族（TripletAttention / BAM / CBAM / SK / PSA）、多段池化/归约流水

## 实现要点
- 合并 launch 的边界：只合并**同相位**分支；跨相位（写后读）合并会触发 507057
- level-0 `uint64_t mask` 是「每 repeat 元素个数」，不是位图；传位图会全例 NaN
- 量化先行：先看「最小 case 时间 ÷ task 数」是否 ≈ 5-10us，再决定是否走这条路

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象（反直觉，先量化再动手）
- 三个读 x 的 kernel（pool_chcw / pool_hw / final）**全是 vector/scalar-bound**：大 case x=67MB 时 mte2 折算只有
- 真正的成本是 **每 device task 的固定开销**：`--quick-batch` 口径把 stream 上所有 task 的 task_time 求和
 （kernel 间隙不计，但每个 kernel 自己的 ramp/epilogue 与 at::zeros 都计入）。实测每 task ≈5-10us：
 最小 case [1,32,11,7] 有效数据仅几 KB，却 97.9us，其中 13 个 task（4 zeros + 9 AIV）；
- 第二成本是 **向量发射条数**：所有逐元素/归约走 `count` 重载的 helper，而 level-0 mask 只有 64 个 fp32 lane，
 （conv+attn+pool_hw 每核发射数 173.2k 条）。

## 有效范围
适用于：纯 AIV、数据量远小于带宽/算力上限、kernel 段数多（≥6）且每段 task 数接近核数的门控/池化类算子
（cv-attn 家族：TripletAttention / BAM / CBAM / SK / PSA 等）。判据：最小 case 的时间 ≈ task 数 × 5-10us，
且 op_statistic 里各 kernel 的 vec/mte2 比值都远低于 1（无 pipe 饱和）。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x121.json`；引用时请结合上文适用条件与失效边界判断适用范围。

