---
type: API
title: Reg矢量计算
description: Reg矢量计算API总览，涵盖数据类型、数据搬入/搬出、MaskReg计算、基础算术、逻辑、归约、同步控制等子模块。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_vector_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Reg矢量计算

AscendC Reg 矢量计算 API 总览，基于寄存器侧 Tensor 执行 SIMD 计算。涵盖寄存器与辅助数据类型、VF 调用、数据搬入/搬出、MaskReg 计算，以及基础算术、逻辑、复合、比较与选择、类型转换、归约、数据填充、离散操作、数据重排、数据压缩、直方图、索引操作、同步控制、系统变量访问等子模块。相比 Memory 版本延迟更低，需配合 Load/Store 使用。
