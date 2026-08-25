---
type: API
title: GetDataBlockSizeInBytes
description: 获取当前芯片版本一个DataBlock的大小，单位为Byte。
tags: [task.lookup, topic.implementation.api_layer.basic_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetDataBlockSizeInBytes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# GetDataBlockSizeInBytes

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取当前芯片版本一个DataBlock的大小，单位为Byte。

开发者根据DataBlock的大小来计算API指令中待传入的repeatTime、dstBlkStride、srcblkStride、dstRepStride、srcRepStride等参数值。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceSum](../../../c_api/vector_compute/asc_datablock_reduce_sum.md)（`related`）：AscDatablockReduceSum 与《GetDataBlockSizeInBytes》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscReduceMinDatablock](../../../c_api/reg/reduce_compute/asc_reduce_min_datablock.md)（`related`）：AscReduceMinDatablock 与《GetDataBlockSizeInBytes》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceDataBlock](../../memory_vector_compute/reduction_compute/reduce_data_block.md)（`related`）：LocalTensor 版块内归约同样以 DataBlock 为单位，GetDataBlockSizeInBytes 可用于计算 repeatTime、stride 和每块元素数量。
- [ReduceDataBlock](../../reg_vector_compute/reduction_compute/reduce_data_block.md)（`related`）：ReduceDataBlock 的每块元素数、mask 范围和结果布局依赖 DataBlock 字节数；查询接口可避免跨架构/类型硬编码。
<!-- cannbot:related:end -->
