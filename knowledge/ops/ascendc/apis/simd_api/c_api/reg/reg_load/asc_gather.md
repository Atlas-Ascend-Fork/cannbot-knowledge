---
type: API
title: AscGather
description: 根据索引位置index将源操作数src按元素收集到目的操作数dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/asc_gather.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscGather

根据索引位置index将源操作数src按元素收集到目的操作数dst中。 图 1  收集UB中的元素 图 2  收集矢量数据寄存器中的元素
函数原型：void asc_gather(vector_int16_t& dst, __ubuf__ int8_t* src, vector_uint16_t index, vector_bool mask)
约束：收集UB中的元素；源操作数在UB中的起始地址需要32B对齐。；对于mask筛选需要搬运的元素，对应的地址需要在UB有效范围内；对于mask未筛选的元素，对应的地址不会触发任何地址越界异常，同时dst中对应的元素将被置零。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
