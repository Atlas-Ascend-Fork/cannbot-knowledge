---
type: Guide
title: 核间负载均衡
description: 通过调整拖尾核位置实现核间负载均衡，避免部分核计算拖尾时其他核空闲，优化多核整体性能。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核间负载均衡

【优先级】：中

【描述】AI处理器的物理核数是固定的，当L2 Cache切分之后，可能发生部分核有计算拖尾的情况，即每次所有核计算量除以每个核处理的数据量不能被核数整除，导致最后需要部分尾核来计算尾块数据。而在尾核计算时，部分核始终处于空闲状态，从而使得算子的整体性能变差。如[图1](#fig26395321518)，假设总的数据量为TotalSize，L2 Cache切分之后分为两份TotalSize / 2，每个核每次的计算量为TotalSize / 2 / 25，即需要25个核进行处理，由于AI处理器的核数为20，因此每次计算时，1到5核的每个核需要多算一份数据，导致发生拖尾的情况。

更详细的多核Tiling切分过程请参见多核Tiling切分。

【反例】

**图1**  计算拖尾示意图

【正例】

针对上述切分策略，调整拖尾核的位置后可以达到全局负载最优，如[图2](#fig133658471154)所示。完成所有计算时，1到10核多一次数据块的计算，可以实现全局负载最优。

**图2**  核间负载均衡示意图
