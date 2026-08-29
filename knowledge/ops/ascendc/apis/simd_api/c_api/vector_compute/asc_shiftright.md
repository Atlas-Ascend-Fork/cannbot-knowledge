---
type: API
title: AscShiftright
description: 对src中的每个元素执行右移，右移大小为value。 - 对于int16_t/int32_t，做算术右移（去掉最低位，最高位复制符号位）。
  - 对于uint16_t/uint32_t，做逻辑右移（去掉最低位，最高位填充为0）。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_shiftright.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscShiftright

对src中的每个元素执行右移，右移大小为value。
函数原型：void asc_shiftright(__ubuf__ int16_t* dst, __ubuf__ int16_t* src, int32_t value, uint32_t count)
约束：value不支持设置为负数。；value取值不能超过src数据类型的位宽。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
