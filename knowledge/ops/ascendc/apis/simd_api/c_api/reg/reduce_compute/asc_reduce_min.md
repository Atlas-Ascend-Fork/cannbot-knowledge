---
type: API
title: AscReduceMin
description: 根据mask对源操作数进行归约最小值操作，将最小值及其索引写入目的操作数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reduce_compute/asc_reduce_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscReduceMin

根据mask对源操作数src进行归约最小值操作，将最小值写入目的操作数dst的第0个元素，将最小值在src中的索引原始位模式写入dst的第1个元素，并将dst中的其他元素置0。如果存在多个最小值，则写入最小的索引。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：float、half、int16_t、int32_t、uint16_t、uint32_t。

约束：- 未被mask选中的元素被视为对应数据类型的最大值，浮点数类型的最大值为+inf。如果src中的所有元素均未被mask选中，则将该最大值写入dst的第0个元素，并将其余元素置0。
- 比较时遵循。
- 如果输入数据中存在nan，则将nan写入dst的第0个元素，并将第一个nan的索引写入dst的第1个元素。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：该卡给出 ReduceMin 向量核异常的复现与平台边界，可用于调用后的故障验证。
- [AscReduceMax](asc_reduce_max.md)（`related`）：AscReduceMax 与《AscReduceMin》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
- [ReduceMin](../../../adv_api/reduction_operations/reduce_min_interface/reduce_min.md)（`related`）：高阶 ReduceMin 封装 shape/workspace，适合整 tensor；Reg API 适合 VF 内显式寄存器归约。
- [ReduceMin](../../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`related`）：Memory Tensor 基础 API 提供 LocalTensor 路径，和 Reg API 的数据驻留、mask 契约不同。
- [ReduceMin接口](../../../adv_api/reduction_operations/reduce_min_interface/reduce_min_interface.md)（`related`）：Reg C API 的 asc_reduce_min 在寄存器编程路径完成相同最小值归约，适合与高阶 Tensor API 按数据驻留位置选型。
- [AscReduceMinDatablock](asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [asc_reduce_min](../../../../simt_api/warp_functions/warp_reduce_functions/asc_reduce_min.md)（`same_topic`）：asc_reduce_min 与《AscReduceMin》的实质衔接是：asc_reduce_min 在同一 warp 的活跃线程间广播最小值；add/max 和 C API 对应入口共享 active-lane 契约，warp reduce 总览补充调用范围。
<!-- cannbot:related:end -->
