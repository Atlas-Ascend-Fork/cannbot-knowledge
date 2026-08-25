---
type: API
title: AscReduceMax
description: 根据mask对源操作数进行归约最大值操作，将最大值及其索引写入目的操作数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscReduceMax

根据mask对源操作数src进行归约最大值操作，将最大值写入目的操作数dst的第0个元素，将最大值在src中的索引原始位模式写入dst的第1个元素，并将dst中的其他元素置0。如果存在多个最大值，则写入最小的索引。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- 未被mask选中的元素被视为对应数据类型的最小值，浮点数类型的最小值为-inf。如果src中的所有元素均未被mask选中，则将该最小值写入dst的第0个元素，并将其余元素置0。
- 比较时遵循。
- 如果输入数据中存在nan，则将nan写入dst的第0个元素，并将第一个nan的索引写入dst的第1个元素。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reg::Reduce 跨 chunk 覆写导致规约失真](../../../../../runbooks/precision/reg_reduce_per_chunk_result_must_accumulate_explicitly.md)（`exemplifies`）：AscReduceMax 与《Reg::Reduce 跨 chunk 覆写导致规约失真》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [AscReduceMin](asc_reduce_min.md)（`related`）：AscReduceMax 与《AscReduceMin》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [ReduceMax接口](../../../adv_api/reduction_operations/reduce_max_interface/reduce_max_interface.md)（`related`）：AscReduceMax说明根据mask对源操作数进行归约最大值操作，将最大值及其索引写入目的操作数。
- [asc_reduce_max](../../../../simt_api/warp_functions/warp_reduce_functions/asc_reduce_max.md)（`related`）：asc_reduce_max 与《AscReduceMax》的实质衔接是：Warp reduce max 与 min/add、C API 对应入口共享 warp 归约契约；padding 元素故障直接约束有效参与数。
- [AscDatablockReduceMax](../../vector_compute/asc_datablock_reduce_max.md)（`same_topic`）：AscReduceMax 与《AscDatablockReduceMax》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [AscGetReduceMaxCnt](../../vector_compute/asc_get_reduce_max_cnt.md)（`same_topic`）：AscReduceMax 与《AscGetReduceMaxCnt》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [AscReduceMaxDatablock](asc_reduce_max_datablock.md)（`same_topic`）：AscReduceMax 与《AscReduceMaxDatablock》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [AscRepeatReduceMax](../../vector_compute/asc_repeat_reduce_max.md)（`same_topic`）：AscReduceMax 与《AscRepeatReduceMax》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [GetReduceMaxMaxMinTmpSize](../../../adv_api/reduction_operations/reduce_max_interface/get_reduce_max_max_min_tmp_size.md)（`same_topic`）：AscReduceMax 与《GetReduceMaxMaxMinTmpSize》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [ReduceMax](../../../adv_api/reduction_operations/reduce_max_interface/reduce_max.md)（`same_topic`）：AscReduceMax 与《ReduceMax》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [ReduceMax](../../../basic_api/memory_vector_compute/reduction_compute/reduce_max.md)（`same_topic`）：AscReduceMax 与《ReduceMax》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
<!-- cannbot:related:end -->
