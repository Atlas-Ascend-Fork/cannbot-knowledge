---
type: API
title: AscGatherDatablock
description: 给定一个输入的矢量和一个地址偏移矢量，根据偏移地址按照DataBlock的粒度将输入矢量收集到目的矢量中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_gather_datablock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscGatherDatablock

给定一个输入的矢量和一个地址偏移矢量，根据偏移地址按照DataBlock的粒度将输入矢量收集到目的矢量中。
函数原型：void asc_gather_datablock(__ubuf__ uint16_t* dst, __ubuf__ uint16_t* src, __ubuf__ uint32_t* src_offset, uint16_t dst_repeat_stride, uint8_t dst_block_stride, uint8_t repeat)
约束：src_offset取值应保证src元素类型位宽对齐。；src加上src_offset偏移后的地址不能超出Unified Buffer (UB)大小数据的范围。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscGatherDatablock](../reg/reg_load/asc_gather_datablock.md)（`same_topic`）：“给定源操作数在UB中的基地址和索引，根据索引位置将源操作数按DataBlock收集到目的操作数中。每个DataBlock长度为32B。 其中，index中仅前8个元素有效，每个元素对应一个DataBlock。”与“给定一个输入的矢量和一个地址偏移矢量，根据偏移地址按照DataBlock的粒度将输入矢量收集到目的矢量中。”提供双方正文证据。两端都以 UB 基址和偏移索引按 DataBlock 收集数据；寄存器版进一步限定 32B 块和前八个索引，向量版给出 LocalTensor 地址偏移入口，互读可完成平台与接口形态选型。
<!-- cannbot:related:end -->
