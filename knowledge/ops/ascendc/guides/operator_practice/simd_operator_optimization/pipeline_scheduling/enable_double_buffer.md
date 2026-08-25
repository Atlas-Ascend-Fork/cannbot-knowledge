---
type: Guide
title: 开启DoubleBuffer
description: 【描述】执行于AI Core上的指令队列主要包括如下几类，Vector指令队列（V）、Cube指令队列（M）、Scalar指令队列（S）和搬运指令队列（MTE1/MTE2/MTE3）。不同指令队列间的相互独立性和可并行执行特性，是DoubleBuffer优化机制的基石。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_double_buffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 开启DoubleBuffer

【优先级】中
【描述】执行于AI Core上的指令队列主要包括如下几类，Vector指令队列（V）、Cube指令队列（M）、Scalar指令队列（S）和搬运指令队列（MTE1/MTE2/MTE3）。不同指令队列间的相互独立性和可并行执行特性，是DoubleBuffer优化机制的基石。
以纯Vector计算为例，矢量计算前后的CopyIn、CopyOut过程使用搬运指令队列（MTE2/MTE3），Compute过程使用Vector指令队列（V），不同指令队列可并行执行，意味着CopyIn、CopyOut过程和Compute过程是可以并行的。如图1所示，考虑一个完整的数据搬运和计算过程，CopyIn过程将数据从Global Memory搬运到Local Memory，Vector计算单元完成Compute计算后，经过CopyOut过程将计算结果搬回Global Memory。
在此过程中，数据搬运与Vector计算串行执行，Vector计算单元不可避免存在资源闲置问题，假设CopyIn、Compute、CopyOut三阶段分别耗时相同均为_t_，则Vector的利用率仅为1/3，等待时间过长，Vector利用率严重不足。
为减少Vector等待时间，开启DoubleBuffer机制将待处理的数据一分为二，例如Tensor1、Tensor2。如图3所示，当Vector单元对Tensor1中数据进行Compute计算时，Tensor2数据流可以执行CopyIn的过程；而当Vector切换到计算Tensor2时，Tensor1数据流可以执行CopyOut的过程。由此，数据的进出搬运和Vector计算实现并行执行，Vector闲置问题得以有效缓解。
总体来说，DoubleBuffer是基于MTE指令队列与Vector指令队列的独立性和可并行性，通过将数据搬运与Vector计算并行执行以隐藏大部分的数据搬运时间，并降低Vector指令的等待时间，最终提高Vector单元的利用效率。通过为队列申请内存时设置内存块的个数为2，开启DoubleBuffer，实现数据并行，简单代码示例如下：
需要注意：
多数情况下，采用DoubleBuffer能有效提升Vector的利用率，缩减算子执行时间。然而，DoubleBuffer机制缓解Vector闲置问题，并不代表它总能带来明显的整体性能提升。例如：
-   当数据搬运时间较短，而Vector计算时间较长时，由于数据搬运在整个计算过程中的时间占比较低，DoubleBuffer机制带来的性能收益会偏小。
-   当原始数据较小且Vector可一次性完成所有数据量的计算时，强行使用DoubleBuffer会降低Vector计算资源的利用率，最终效果可能适得其反。
因此，DoubleBuffer的使用需综合考虑Vector算力、数据量大小、搬运与计算时间占比等多种因素。
【反例】
【正例】

<!-- cannbot:related:start -->
## 相关

- [DoubleBuffer](../../../technical_appendix/concepts_and_terms/performance_optimization/double_buffer.md)（`related`）：概念卡解释流水并行基础，EnableDoubleBuffer 给出通过队列深度与 tiling 开启搬入/计算重叠的落地方法。
- [FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR](../../../../runbooks/compilation/fp16_double_buffer_ub_budget_queue_vs_tbuf_multiplier.md)（`related`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《开启DoubleBuffer》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](../../../../runbooks/compilation/elementwise_tque_double_buffer_inplace_recipe.md)（`related`）：HardSwish 配方给出已验证的两个 TQue、BUFFER_NUM=2、in-place Compute 与单 tile 快路径，提供 DoubleBuffer 在逐元素 kernel 中的具体实现和 UB 算式。
- [SIMD算子实现概述](../../simd_operator_impl/vector_programming/overview.md)（`related`）：焦点处理SIMD 算子实现总览中的双缓冲和计算模型；开启DoubleBuffer正文界定“【描述】执行于AI Core上的指令队列主要包括如下几类，Vector指令队列（V）、Cube指令队列（M）、Scalar指令队列（S）和搬运指令队列（MTE1/MTE2/MTE3）。不同指令队列间的相互独立性和可并行执行特性，是Doubl”。候选只保留与总览正文直接展开的 SIMD 计算、DoubleBuffer 机制及其重复说明。
- [启用Iterate或IterateAll异步接口避免AIC/AIV同步依赖](enable_iterate_avoid_sync.md)（`related`）：异步 Iterate 减少 Cube/Vector 等待，双缓冲用于覆盖搬运与计算，常组合使用。
- [DoubleBuffer场景](../../simd_operator_impl/vector_programming/double_buffer_scenario.md)（`same_topic`）：DoubleBuffer场景 与《开启DoubleBuffer》的实质衔接是：DoubleBuffer 将主块拆为两份并通过 InitBuffer(...,2,...) 让搬入、计算、搬出重叠；主尾块切分材料说明尾块例外，UB 预算和 TQue/TBuf 重载故障直接约束 bufferNum 与长度配置。
- [核间负载均衡](../tiling_strategy/inter_core_load_balance.md)（`same_topic`）：核间负载均衡 与《开启DoubleBuffer》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
