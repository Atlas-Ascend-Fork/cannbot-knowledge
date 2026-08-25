---
type: API
title: AscFloat2Int32
description: 将float类型转换为int32_t类型，支持RINT、ROUND、FLOOR、CEIL四种舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_float2int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscFloat2Int32

将float类型转化为int32_t类型，并支持多种舍入模式。 舍入模式：
函数原型：int32_t asc_float2int32_rn(float value)
返回值：目的操作数（标量），value精度转换成int32_t的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
