---
type: API
title: AscAxpy
description: 源操作数src中每个元素与标量value求积后和目的操作数dst中的对应元素相加
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_axpy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAxpy

源操作数src中每个元素与标量value求积后和目的操作数dst中的对应元素相加计算公式如下：
函数原型：void asc_axpy(__ubuf__ half* dst, __ubuf__ half* src, half value, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
