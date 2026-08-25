---
type: API
title: 逻辑计算
description: Memory矢量计算逻辑运算接口索引页，汇总Not、And、Or、Ands、Ors及ShiftLeft/ShiftRight系列。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/logical_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 逻辑计算

Memory 矢量逻辑运算接口集合，包含按位逻辑（Not、And、Or、Ands、Ors，带 s 后缀为标量版本）与移位运算（ShiftLeft、ShiftRight，移位数可为标量或 Tensor）。用于整数类型的位操作场景，需注意操作数数据类型与 mask 配置。

<!-- cannbot:related:start -->
## 相关

- [逻辑计算](../../reg_vector_compute/logical_compute/logical_compute.md)（`related`）：两张逻辑计算概述分别说明 RegTensor 与 UB Memory 的逻辑运算模型，可用于决定是否采用寄存器 mask 流程或连续/高维 UB 流程。
<!-- cannbot:related:end -->
