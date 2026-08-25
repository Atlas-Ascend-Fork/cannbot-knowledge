---
type: API
title: 数据重排
description: Reg矢量计算数据重排接口索引页，包含Interleave与DeInterleave。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_reorder/data_reorder.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 数据重排

提供 Interleave 和 DeInterleave 接口，用于寄存器级元素交织与解交织。Interleave 将 srcReg0 和 srcReg1 中的元素交织存入 dstReg0 和 dstReg1，DeInterleave 为其逆操作。

操作数为 RegTensor 类型，由编译器自动推导。仅 Ascend 950PR/Ascend 950DT 支持，需在 VF 函数内调用。
