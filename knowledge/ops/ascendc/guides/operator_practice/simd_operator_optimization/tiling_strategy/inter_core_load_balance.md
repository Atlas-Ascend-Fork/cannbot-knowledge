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

<!-- cannbot:related:start -->
## 相关

- [核间同步](../../../../apis/simd_api/basic_api/sync_control/inter_core_sync/inter_core_sync.md)（`explains`）：核间负载均衡 与《核间同步》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [核间同步能力概述](../../../../apis/simd_api/basic_api/sync_control/inter_core_sync/inter_core_sync_overview.md)（`explains`）：核间负载均衡 与《核间同步能力概述》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [多核 numPerCore 须对齐 Philox group 4](../../../../runbooks/precision/numpercore_philox_group_4.md)（`related`）：核间负载均衡 与《多核 numPerCore 须对齐 Philox group 4》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [Matmul算子优化Tiling策略](../../best_practices/matmul_tuning_cases/matmul_tiling_strategy.md)（`same_topic`）：核间负载均衡 与《Matmul算子优化Tiling策略》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [SIMD算子优化概述](../memory_access/avoid_ub_bank_conflict/overview.md)（`same_topic`）：核间负载均衡 与《SIMD算子优化概述》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [优化建议总览表（SIMD算子优化）](../optimization_summary.md)（`same_topic`）：核间负载均衡 与《优化建议总览表（SIMD算子优化）》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](../pipeline_scheduling/enable_iterate_avoid_sync.md)（`same_topic`）：核间负载均衡 与《启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [开启DoubleBuffer](../pipeline_scheduling/enable_double_buffer.md)（`same_topic`）：核间负载均衡 与《开启DoubleBuffer》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [设置合适的核数和算子Kernel类型](../overhead_optimization/core_count_kernel_type.md)（`same_topic`）：核间负载均衡 与《设置合适的核数和算子Kernel类型》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
