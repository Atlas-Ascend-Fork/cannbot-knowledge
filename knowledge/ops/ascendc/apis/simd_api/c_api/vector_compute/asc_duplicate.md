---
type: API
title: AscDuplicate
description: 执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscDuplicate

执行矢量复制（Duplicate）操作，将标量值复制填充到矢量中。
函数原型：void asc_duplicate(__ubuf__ half* dst, half src, uint32_t count)
约束：dst的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等
