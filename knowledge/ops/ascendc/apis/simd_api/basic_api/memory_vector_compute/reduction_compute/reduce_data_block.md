---
type: API
title: ReduceDataBlock
description: 对输入数据以DataBlock为单位进行归约操作，根据reduceType对每个DataBlock内数据求和、求最大值或求最小值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/reduction_compute/ReduceDataBlock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceDataBlock

对输入数据以DataBlock为单位进行归约操作，根据reduceType对每个DataBlock内数据求和、求最大值或求最小值。

本接口用于在矢量计算时设置mask。 - 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用SetMaskCount/SetMaskNorm手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同： - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式： - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈[0, 128]；当操作数为32位时，mask∈[0, 64]；当操作数为64位时，mask∈[0, 32]。 - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh

本接口组包含 SetVectorMask, LocalTensor, LocalTensor, 掩码概述, 高维切分。

本接口属于 UB 矢量计算归约接口。

约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [选择低延迟指令，优化归约操作性能](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/low_latency_instruction.md)（`explains`）：指南比较两次 ReduceRepeat、三次 ReduceDataBlock 和二者组合，结论是先 ReduceDataBlock 再 ReduceRepeat 在 shape=256 的实测更优。
- [GetDataBlockSizeInBytes](../../tool_interface/system_resources_and_variables/get_data_block_size_in_bytes.md)（`related`）：LocalTensor 版块内归约同样以 DataBlock 为单位，GetDataBlockSizeInBytes 可用于计算 repeatTime、stride 和每块元素数量。
- [ReduceDataBlock](../../reg_vector_compute/reduction_compute/reduce_data_block.md)（`related`）：Memory Vector ReduceDataBlock 与 Reg 版本都按每个 32B DataBlock 输出 SUM/MAX/MIN；Reg 卡补充 MaskMergeMode 和全 mask 空时的填充值，是切换编程范式的直接契约映射。
- [ReduceRepeat](reduce_repeat.md)（`related`）：DataBlock 归约粒度小于 per-repeat，按输出粒度选择。
- [AscDatablockReduceSum](../../../c_api/vector_compute/asc_datablock_reduce_sum.md)（`same_topic`）：AscDatablockReduceSum 与《ReduceDataBlock》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscReduceMinDatablock](../../../c_api/reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceDataBlock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceMin](reduce_min.md)（`same_topic`）：ReduceMin 与《ReduceDataBlock》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
<!-- cannbot:related:end -->
