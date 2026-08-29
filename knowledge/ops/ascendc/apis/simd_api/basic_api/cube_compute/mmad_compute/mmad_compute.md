---
type: API
title: 矩阵计算（ISASI）
description: 矩阵计算 ISASI Mmad 接口集，包含 Mmad、MmadMx、MmadBitMode、MmadWithSparse 等矩阵乘计算接口。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/mmad_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵计算（ISASI）

ISASI Cube 矩阵乘计算接口集合，提供 Mmad、MmadMx、MmadBitMode、MmadWithSparse 等矩阵乘算子。Mmad 为标准矩阵乘；MmadMx 支持混合精度输入；MmadBitMode 面向低比特量化场景；MmadWithSparse 用于稀疏矩阵乘。Conv2D、Gemm 接口已废弃，应使用对应新接口替代。接口作用对象为 Cube 单元，使用前需确认 K 方向对齐与数据类型约束。
