---
type: API
title: asc_popc（标量计算）
description: 获取一个uint64_t类型数字的二进制中1的个数。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_popc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_popc（标量计算）

获取一个uint64_t类型数字的二进制中1的个数。
函数原型：int64_t asc_popc(uint64_t value)
参数：value（输入）：被统计的二进制数字。
返回值：value的二进制中1的个数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
