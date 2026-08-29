---
type: API
title: asc_ffz（标量计算）
description: 获取一个uint64_t类型数字的二进制表示中从最低有效位开始的第一个0出现的位置，如果没找到则返回-1。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_ffz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_ffz（标量计算）

获取一个uint64_t类型数字的二进制表示中从最低有效位开始的第一个0出现的位置，如果没找到则返回-1。
函数原型：int64_t asc_ffz(uint64_t value)
参数：value（输入）：输入数据，数据类型是uint64_t。
返回值：value中第一个0出现的位置。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等
