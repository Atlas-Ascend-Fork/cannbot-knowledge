---
type: Guide
title: MemoryAccessMerge
description: SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simt_operator_optimization/memory_access/memory_access_merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 访存合并

【优先级】高
【描述】SIMT编程模式下，一个Warp内的相邻线程（thread）通常同时发起GM访问请求。若这些线程访问的GM地址连续，硬件可以将访问请求合并，从而提高GM带宽利用率；若相邻线程访问的GM地址跨行或离散分布，则难以形成访存合并，算子执行耗时会明显增加。对于转置、重排、gather/scatter等算子，需要结合数据排布和线程映射关系进行分析，尽量让同一个Warp内相邻线程在同一条访存指令上访问连续地址。
访存合并优化适用于两类场景：第一类是数据本身在GM上连续，只是相邻thread被分配处理的数据不连续，导致同一个Warp内相邻线程访问了不连续地址，此时优先调整数据切分方式，使Warp内相邻thread访问连续数据；第二类是算子功能包含转置、重排等布局变换，单纯调整切分方式很难同时保证GM读写都连续，此时考虑引入UB内存空间作为中转，利用UB完成不连续的数据重排过程，从而尽量保证GM侧访问连续。
- 优化数据切分实现访存合并
【样例介绍】以Gather算子为例，算子按行从输入中取数，计算公式可以表示为output[row, col] = input[index[row], col]。输出矩阵每一行内部的列方向数据在GM上连续，优化切分时应让同一个Warp内相邻线程尽量访问同一行内的相邻列，而不是只保证单个线程内部连续。
【反例】按thread切分数据，每个thread处理连续的一行数据。
上述实现把输出行分配给不同thread，每个thread在for循环内连续处理一整行数据。从单个thread视角看，input_idx和output_idx都是连续递增的；但SIMT访存合并的关键是同一个Warp内相邻thread在同一条访存指令上访问的地址连续。在该实现中，同一个Warp内的相邻thread分别处理不同的out_row，虽然单个thread内部访问连续，但Warp内访问不连续，GM访存难以合并。
以输入shape为20001×1023，index长度为核数乘以2048为例，线程块总数与物理核数相等，每个线程块启动2048个线程，反例算子执行该用例的性能数据如下：
Task Duration(us)：aiv_time(us)：aiv_total_cycles：aiv_vec_time(us)：aiv_vec_ratio：aiv_scalar_time(us)：aiv_scalar_ratio
4886.076：4535.644：7483813.083：4535.178：0.999：0.454：0.001
【正例】按Thread Block切分输出数据，Warp内相邻thread访问连续地址。

<!-- cannbot:related:start -->
## 相关

- [访存函数简介（内存访问函数）](../../../../apis/simt_api/memory_access_functions/memory_access_functions_intro.md)（`explains`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《访存函数简介（内存访问函数）》提供“SIMT编程通常需要大量Thread并行访问Global Memory。访存函数用于显式控制Global Memory访问时的缓存路径和缓存一致性维护方式，帮助开发者根据数据复用特征、写回方式和跨核可见性要求选择合适的加载、存储或Cache刷新接口。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [DCacheAccess](dcache_access.md)（`related`）：缓存驻留优化解决热点复用，访存合并解决 Warp 地址连续性；两者同时决定 GM/DCache 有效带宽，不能用其中一个代替另一个。
- [通过类型对齐提升搬运效率](type_alignment_transfer.md)（`related`）：类型对齐提高单线程访问位宽，访存合并则要求同一 Warp 相邻线程地址连续；两者必须同时满足才能把宽访问合并成高带宽 GM 事务。
- [EfficientTransferApi](../../simd_operator_optimization/memory_access/efficient_transfer_api.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《EfficientTransferApi》提供“使用搬运API时应通过配置搬运控制参数实现连续或固定间隔搬运，避免使用for循环，提升搬运效率。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [GM地址尽量512B对齐](../../simd_operator_optimization/memory_access/gm_address_512b_alignment.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《GM地址尽量512B对齐》提供“【描述】由于AI处理器内部设计约束，从GM向Local Memory搬运数据时，保证GM地址512B对齐可以最有效的发挥出带宽的效率。如下图示例，展示了在512B对齐以及32B对齐情况下单核的带宽效率：搬运同等数据量，带宽差距最大的情况，32B对齐场景只能达到512B对齐场景的70%。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [Gather算子快速入门](../../../getting_started/quick_start/simt_programming/gather_op_quick_start.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《Gather算子快速入门》提供“本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [SIMT算子优化概述](../overview.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《SIMT算子优化概述》提供“SIMT编程模式以线程（Thread）为基本编程单位，由开发者编写单个线程的执行逻辑，再通过>>配置将大量线程组织为线程块（线程块）与线程网格（Grid），调度到硬件的Vector Core（物理核，即AIV核）上以Warp为单位并行执行。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [ShortVectorEfficiency](short_vector_efficiency.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《ShortVectorEfficiency》提供“SIMT编程模式下使用短向量类型替代普通数据类型进行数据搬运和计算，覆盖整个Cache Line，提升访存效率。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [尽量一次搬运较大的数据块](../../simd_operator_optimization/memory_access/transfer_larger_data_blocks.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《尽量一次搬运较大的数据块》提供“【描述】搬运不同大小的数据块时，对带宽的利用率（有效带宽/理论带宽）不一样。根据实测经验，单次搬运数据长度16KB以上时，通常能较好地发挥出带宽的最佳性能。因此对于单次搬运，应考虑尽可能的搬运较大的数据块。下图展示了某款AI处理器上实测的不同搬运数据量下带宽的变化图。”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [算子实现（SIMT算子实现）](../../simt_operator_impl/operator_impl.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《算子实现（SIMT算子实现）》提供“本章节将以Gather类算子为例，介绍SIMT算子实现的基本流程，如下图所示：”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [避免同地址访问](../../simd_operator_optimization/memory_access/avoid_same_address_access.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《避免同地址访问》提供“>该性能优化指导适用于如下产品型号：”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [非对齐场景减少无效数据的搬运](../../simd_operator_optimization/memory_access/reduce_invalid_data_transfer.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《非对齐场景减少无效数据的搬运》提供“>该性能优化建议适用于如下型号：”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
- [非连续搬运场景减少搬运次数](../../simd_operator_optimization/memory_access/reduce_non_contiguous_transfer.md)（`same_topic`）：《MemoryAccessMerge》处理“SIMT编程模式下让同一Warp内相邻线程访问连续GM地址以实现访存合并，提高GM带宽利用率。”。《非连续搬运场景减少搬运次数》提供“>该性能优化建议适用于如下产品型号：”，其具体合同或探针直接接入Warp 连续 GM 访问的短向量、类型对齐、步长搬运和 Gather 示例验证。
<!-- cannbot:related:end -->
