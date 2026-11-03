---
type: Guide
title: Atlas A2系列产品和Atlas A3系列产品 Stage 设计规则
description: Atlas A2系列产品和Atlas A3系列产品的独立 Stage、MemBase、GM（用户 workspace）中转和流水规则。
tags:
- task.design
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/pull/1274
  role: primary
- resource: https://gitcode.com/cann/catlass/tree/0d78a73c192fc04741a4fd57c94080209424775c
  role: supporting
created_at: '2026-10-18T00:00:00Z'
updated_at: '2026-10-26T17:17:23Z'
platforms:
- a2
- a3
verified:
- by: process:architecture-separation-source-check
  at: '2026-10-18T00:00:00Z'
---
# Atlas A2系列产品和Atlas A3系列产品 Stage 设计规则

仅当 `target_architecture=atlas_a2_a3` 时读取本文件。本文件完整定义 Atlas A2系列产品和
Atlas A3系列产品的独立规则集，不从其它芯片文件继承或补齐规则。组件和 API 必须核对当前固定版本
源码；模型 case 不能代替完整支持域，参考容量和候选方案不能代替目标 SoC 的能力与实测证据。
规则基线与架构能力来源见脚注。[^pr1069-stage-design-rules][^catlass-arch-separation]

## 完整规则

### R01 Stage 计算类型

每个 Stage 只包含 Cube 或 Vector 一类操作，可以包含多个同类型操作。

### R02 Stage 划分

存在 Cube 数据依赖的 Cube 操作必须划分到不同 Cube Stage。

除上述强制边界外，连续同类操作默认合并；只有拆分后能让其它执行单元或相邻任务提前推进，
或者合并后超过片上存储容量时，才拆分 Stage。

### R03 多任务 Stage 推进

分别确定每批包含多少个任务，以及同一时刻有多少批任务在流水中推进；
比较不同组合，选择执行单元空闲、重复搬运和同步开销更少的方案。

### R04 Cube/Vector Stage 间数据通路

A2/A3 的 Cube 与 Vector 中间结果通过 GM（用户 workspace）交接。
按生产消费生命周期确定中转空间；同时存活的结果地址不得重叠。

### R05 同执行单元中间结果复用

后续仍由同一 AIV 使用的 Vector 结果优先保留在 UB，
后续仍由 AIC 使用的 Cube 结果优先保留在 L1。

是否继续保留，结合复用间隔、数据大小、片上空间占用，
以及重新搬运或重新计算的成本确定。

### R06 缓冲空间份数

下一份同类数据可与当前数据的消费并行时，为同时处理的数据分配不同缓冲空间；
缓冲份数由生产消费速度、并行任务数、单份数据大小和可用空间决定。
若仅因同步位置阻断并行，先调整同步。

### R07 片上存储容量

按数据生命周期分配并复用片上地址。
分别计算每个 AIV 的 UB，以及每个 AIC 的 L1、L0A、L0B、L0C 使用峰值；
各峰值不得超过对应的可用容量。

没有依赖关系的 Cube Stage 和 Vector Stage 可能并行执行，
其同时存活的数据必须一起计入峰值，地址不得重叠。

### R08 GM 搬运的 L2 Cache

每次 GM 搬运独立决定是否使能 L2 Cache。当前 kernel 内只访问一次且没有复用的数据可以不使能；
会被重复访问、跨 Stage 交接或被多个执行单元消费的数据应使能。

### R09 数值稳定性检查

逐项分析高风险运算的计算 dtype、输入和中间值范围、溢出/下溢、`NaN/Inf`、cast 与 mask 时机。
代数变换必须证明值域、误差和溢出风险保持或改善；无效位置在高风险运算前排除或替换为安全值。

[^pr1069-stage-design-rules]: git:cann/cannbot-skills@4950cbd7c45e0d44cb8ec52598edf53cdc7f16ca:ops/catlass-linear-attention-workflow/references/stage_design_rules.md

[^catlass-arch-separation]: https://gitcode.com/cann/catlass/blob/0d78a73c192fc04741a4fd57c94080209424775c/include/catlass/gemm/tile/copy_l0c_to_gm.hpp
