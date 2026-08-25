---
type: API
title: ReduceMin
description: 从所有输入数据中找出最小值，可选返回最小值索引。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/ReduceMin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceMin

从所有输入数据中找出最小值，可选返回最小值索引。

ReduceMin接口用于从所有输入数据中找出最小值和最小值索引。 ReduceMin计算过程如下图所示：首先，在每个repeat迭代中计算得到最小值和repeat内部索引，这些中间结果暂存于sharedTmpBuffer工作区中；然后，在中间结果的基础上继续按repeat迭代得到最终的最小值和最小值索引。需要注意的是，每次repeat迭代获取的最小值索引是repeat内部索引，返回最终结果时，需要根据迭代位置和repeat内部索引推导全量数据的最小值索引。 图1 ReduceMin计算示意图

本接口属于 UB 矢量计算接口。

参数说明：T：操作数数据类型。；dst：输出 目的操作数。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT。；src：输入 源操作数。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT。；sharedTmpBuffer：输入 指令执行期间存储中间结果，用于内部计算所需操作空间，需特别注意空间大小。详情请参考[关键特性说明](#关键特性说明)。 类型为LocalTensor，支持的TPosition为VECIN、VECCALC、VECOUT。；count：输入 参与计算的元素个数。关于该参数的具体说明请参考[连续计算](../simd_compute/continuous_compute.md)。最大处理的数据量不能超过UB大小限制。

约束：源操作数及sharedTmpBuffer的地址对齐约束请参考通用地址对齐约束，起始地址需要32字节对齐；目的操作数的起始地址对齐约束请参考ReduceRepeat-表3。；操作数地址重叠约束请参考通用地址重叠约束。；需要使用sharedTmpBuffer的情况下，支持dst与sharedTmpBuffer地址重叠（通常情况下dst比sharedTmpBuffer所需的空间要小），此时sharedTmpBuffer必须满足所需空间要求，详情请参考关键特性说明。；当参数count或repeatTime取值为0时，该接口的行为如下：

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：ReduceMin 与《A5 循环内 ReduceMin 取索引致 vector core 异常》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [如何使用归约计算API](../../../../../guides/programming_guide/library_api/basic_api/quick_reference/how_to_use_reduction_api.md)（`explains`）：ReduceMin 与《如何使用归约计算API》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [AscReduceMin](../../../c_api/reg/reduce_compute/asc_reduce_min.md)（`related`）：Memory Tensor 基础 API 提供 LocalTensor 路径，和 Reg API 的数据驻留、mask 契约不同。
- [Reduce](../../reg_vector_compute/reduction_compute/reduce.md)（`related`）：Reg::Reduce 的 MIN 与 ReduceMin 都完成最小值归约，但分别面向寄存器编程和 LocalTensor 内存向量接口。
- [ReduceMax](reduce_max.md)（`related`）：ReduceMin 聚合方向相反，按目标极值选。
- [ReduceMin接口](../../../adv_api/reduction_operations/reduce_min_interface/reduce_min_interface.md)（`related`）：基础 Tensor ReduceMin 提供更低层的归约实现路径，可据 shape、mask 和临时空间需求与高阶接口选型。
- [AscDatablockReduceMin](../../../c_api/vector_compute/asc_datablock_reduce_min.md)（`same_topic`）：ReduceMin 与《AscDatablockReduceMin》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [AscGetReduceMinCnt](../../../c_api/vector_compute/asc_get_reduce_min_cnt.md)（`same_topic`）：ReduceMin 与《AscGetReduceMinCnt》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [AscReduceMinDatablock](../../../c_api/reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscRepeatReduceMin](../../../c_api/vector_compute/asc_repeat_reduce_min.md)（`same_topic`）：ReduceMin 与《AscRepeatReduceMin》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [GetReduceMinMaxMinTmpSize](../../../adv_api/reduction_operations/reduce_min_interface/get_reduce_min_max_min_tmp_size.md)（`same_topic`）：ReduceMin 与《GetReduceMinMaxMinTmpSize》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [GetReduceRepeatMaxMinSpr](../reduction_compute_aux_config/get_reduce_repeat_max_min_spr_isasi.md)（`same_topic`）：ReduceMin 与《GetReduceRepeatMaxMinSpr》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [ReduceDataBlock](reduce_data_block.md)（`same_topic`）：ReduceMin 与《ReduceDataBlock》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [ReduceMin](../../../adv_api/reduction_operations/reduce_min_interface/reduce_min.md)（`same_topic`）：ReduceMin 与《ReduceMin》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [ReduceRepeat](reduce_repeat.md)（`same_topic`）：ReduceMin 与《ReduceRepeat》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [asc_reduce_min](../../../../simt_api/warp_functions/warp_reduce_functions/asc_reduce_min.md)（`same_topic`）：ReduceMin 与《asc_reduce_min》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约计算](reduction_compute.md)（`same_topic`）：ReduceMin 与《归约计算》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约计算](../../reg_vector_compute/reduction_compute/reduction_compute.md)（`same_topic`）：ReduceMin 与《归约计算》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [归约计算概述](introduction.md)（`same_topic`）：ReduceMin 与《归约计算概述》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
<!-- cannbot:related:end -->
