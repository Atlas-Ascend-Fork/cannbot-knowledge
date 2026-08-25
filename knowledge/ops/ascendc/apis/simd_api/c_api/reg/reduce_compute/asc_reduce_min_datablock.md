---
type: API
title: AscReduceMinDatablock
description: 根据mask将每个DataBlock中的最小值依次保存在目的操作数的最低位。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_min_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscReduceMinDatablock

根据mask将每个DataBlock(32B)中的最小值依次保存在dst中的最低位。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- 在比较中，遵循min(-0, +0) = -0。
- 找到源操作数中每个DataBlock内的最小值，连续写入到目的操作数，目的操作数中的其它元素置0。
- 未被mask选中的元素被视为最大值（浮点数为+inf），如果一个DataBlock中所有元素都未被mask选中，+inf将被填充到目的操作数的指定位置。
- 仅输出最值，不输出index下标。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：AscReduceMinDatablock 与《A5 循环内 ReduceMin 取索引致 vector core 异常》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [GetDataBlockSizeInBytes](../../../basic_api/tool_interface/system_resources_and_variables/get_data_block_size_in_bytes.md)（`related`）：AscReduceMinDatablock 与《GetDataBlockSizeInBytes》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscDatablockReduceMin](../../vector_compute/asc_datablock_reduce_min.md)（`same_topic`）：AscReduceMinDatablock 与《AscDatablockReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscGetReduceMinCnt](../../vector_compute/asc_get_reduce_min_cnt.md)（`same_topic`）：AscReduceMinDatablock 与《AscGetReduceMinCnt》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscReduceMaxDatablock](asc_reduce_max_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscReduceMaxDatablock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscReduceMin](asc_reduce_min.md)（`same_topic`）：AscReduceMinDatablock 与《AscReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscReduceSumDatablock](asc_reduce_sum_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscReduceSumDatablock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [AscRepeatReduceMin](../../vector_compute/asc_repeat_reduce_min.md)（`same_topic`）：AscReduceMinDatablock 与《AscRepeatReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceDataBlock](../../../basic_api/memory_vector_compute/reduction_compute/reduce_data_block.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceDataBlock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceDataBlock](../../../basic_api/reg_vector_compute/reduction_compute/reduce_data_block.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceDataBlock》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceMin](../../../adv_api/reduction_operations/reduce_min_interface/reduce_min.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceMin](../../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：AscReduceMinDatablock 与《ReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [asc_reduce_min](../../../../simt_api/warp_functions/warp_reduce_functions/asc_reduce_min.md)（`same_topic`）：AscReduceMinDatablock 与《asc_reduce_min》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
<!-- cannbot:related:end -->
