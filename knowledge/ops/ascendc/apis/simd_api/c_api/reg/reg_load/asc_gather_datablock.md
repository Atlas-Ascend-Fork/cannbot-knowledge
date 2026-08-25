---
type: API
title: AscGatherDatablock
description: 根据索引将UB中的源操作数按32B的DataBlock收集到目的操作数中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_gather_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscGatherDatablock

给定源操作数在UB中的基地址和索引，根据索引位置将源操作数按DataBlock收集到目的操作数中。每个DataBlock长度为32B。 其中，index中仅前8个元素有效，每个元素对应一个DataBlock。例如，第一个元素为96（3 * 32），表示选取DataBlock3写入dstReg中对应的位置。
函数原型：void asc_gather_datablock(vector_int4x2_t& dst, __ubuf__ int4b_t* src, vector_uint32_t index, vector_bool mask)
约束：源操作数在UB中的起始地址需要32B对齐。；索引位置要大于等于0且32B对齐，即一个索引值对应一个DataBlock。；索引可以存在相同的值，即可以多次读取源操作数中同一个DataBlock的数据。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [GatherB](../../../basic_api/reg_vector_compute/reg_data_load/gather_b_discrete.md)（`related`）：两接口都按偏移寄存器离散收集 8 个 32B datablock，分别是 ISASI/Reg 与 C API 表面，可用于同一 gather-block 需求迁移。
- [AscGather](asc_gather.md)（`same_topic`）：《AscGather》明确“根据索引位置index将源操作数src按元素收集到目的操作数dst中。”；它与《AscGatherDatablock》的“根据索引将UB中的源操作数按32B的DataBlock收集到目的操作数中。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscGatherDatablock](../../vector_compute/asc_gather_datablock.md)（`same_topic`）：《AscGatherDatablock》明确“给定一个输入的矢量和一个地址偏移矢量，根据偏移地址按照DataBlock的粒度将输入矢量收集到目的矢量中。”；它与《AscGatherDatablock》的“根据索引将UB中的源操作数按32B的DataBlock收集到目的操作数中。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
