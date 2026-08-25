---
type: API
title: Reg矢量计算索引操作
description: 寄存器矢量索引操作接口集合，包含Arange接口。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/index_operations/index_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg矢量计算索引操作

提供 Arange 接口，在寄存器中生成递增或递减索引序列。递增模式以 scalarValue 为起始值生成递增索引，递减模式以 scalarValue 为终止值生成递减索引，结果保存在 dstReg 中。

通过模板参数 IndexOrder 选择 INCREASE_ORDER 或 DECREASE_ORDER 模式。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
