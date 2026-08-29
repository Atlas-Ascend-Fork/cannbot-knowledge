---
type: API
title: Reg矢量计算离散操作
description: 寄存器矢量离散操作接口集合，包含Gather接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/scatter_operations/scatter_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg矢量计算离散操作

提供 Gather 接口，根据索引值 indexReg 将源操作数 srcReg 按元素收集到目的操作数 dstReg 中。indexReg 数据类型位宽需与目的操作数一致，索引值可重复。

当索引值超出 RegTensor 最大元素个数（VL/sizeof(T)）时，按取模方式更新索引。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
