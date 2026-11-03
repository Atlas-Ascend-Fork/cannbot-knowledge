---
type: Guide
title: Ascend 950PR&950DT系列产品 Stage 设计规则
description: Ascend 950PR&950DT系列产品的独立 Stage、RegBase/VF、直连和片上存储规则。
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
- '950'
verified:
- by: process:architecture-separation-source-check
  at: '2026-10-18T00:00:00Z'
---
# Ascend 950PR&950DT系列产品 Stage 设计规则

仅当 `target_architecture=ascend950` 时读取本文件。本文件完整定义 Ascend 950PR&950DT系列产品
的独立规则集，不从其它芯片文件继承或补齐规则。组件和 API 必须核对当前固定版本源码；模型 case
不能代替完整支持域，参考容量和候选方案不能代替目标 SoC 的能力与实测证据。
规则基线与架构能力来源见脚注。[^pr1069-stage-design-rules][^catlass-arch-separation]

## 完整规则

### R01 Stage 计算类型

每个 Stage 只包含 Cube 或 Vector 一类操作，可以包含多个同类型操作。

### R02 Stage 划分

存在 Cube 数据依赖的 Cube 操作必须划分到不同 Cube Stage。

除上述强制边界外，连续同类操作默认合并；只有拆分后能让其它执行单元或相邻任务提前推进，
或者合并后超过片上存储容量时，才拆分 Stage。

### R03 Vector VF 合并

同一 Vector Stage 优先用一次 VF 完成；一次 VF 无法正确实现、资源超限或阻塞流水时，
采用满足要求的最少 VF 次数，避免因分段搬运增加 VF 调用。

### R04 多任务 Stage 推进

分别确定每批包含多少个任务，以及同一时刻有多少批任务在流水中推进；
比较不同组合，选择执行单元空闲、重复搬运和同步开销更少的方案。

### R05 Cube/Vector Stage 间数据通路

Cube/Vector 中间结果在组件支持且不阻塞流水时优先直连，否则通过 GM（用户 workspace）中转。
采用 GM（用户 workspace）中转时，按生产消费生命周期确定中转空间；同时存活的结果地址不得重叠。

### R06 同执行单元中间结果驻留

同一执行单元后续仍需使用的中间结果，AIV 同一 VF 内优先保留在寄存器、跨 VF 优先保留在 UB，
AIC 优先保留在 L1。

是否驻留取决于复用间隔、空间占用及重新搬运或计算的成本。寄存器驻留以编译结果为准；
编译器将数据暂存到 UB 时，应计入 UB 空间和搬运成本。[^reg-vector-model]

### R07 缓冲空间份数

相邻数据的搬入、计算或搬出可以并行时，至少使用双缓冲；双缓冲轮转后仍需等待缓冲区释放时，
再增加份数。若同步阻断本可并行的操作，先调整同步。

### R08 片上存储容量

按数据生命周期分配并复用片上地址。
分别计算每个 AIV 的寄存器和 UB，以及每个 AIC 的 L1、L0A、L0B、L0C、FixBuf 使用峰值；
各峰值不得超过目标芯片对应的可用容量，寄存器容量以编译结果校验。

没有依赖关系的 Cube Stage 和 Vector Stage 可能并行执行，
其同时存活的数据必须一起计入峰值，地址不得重叠。

### R09 GM 搬运的 L2 Cache

每次 GM 搬运独立决定是否使能 L2 Cache。当前 kernel 内只访问一次且没有复用的数据可以不使能；
会被重复访问、跨 Stage 交接或被多个执行单元消费的数据应使能。直连路径不涉及 L2 Cache。

### R10 数值稳定性检查

逐项分析高风险运算的计算 dtype、输入和中间值范围、溢出/下溢、`NaN/Inf`、cast 与 mask 时机。
代数变换必须证明值域、误差和溢出风险保持或改善；无效位置在高风险运算前排除或替换为安全值。

[^pr1069-stage-design-rules]: git:cann/cannbot-skills@4950cbd7c45e0d44cb8ec52598edf53cdc7f16ca:ops/catlass-linear-attention-workflow/references/stage_design_rules.md

[^catlass-arch-separation]: https://gitcode.com/cann/catlass/blob/0d78a73c192fc04741a4fd57c94080209424775c/include/catlass/gemm/tile/copy_l0c_to_ub.hpp

[^reg-vector-model]: CANN 9.2.0-beta.1，编程模型概述与 Reg 矢量计算；https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/920beta1/programug/Ascendcopdevg/docs/zh/guide/编程指南/编程模型/编程模型概述.md
