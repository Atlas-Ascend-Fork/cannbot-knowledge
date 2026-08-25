---
type: API
title: Mmad计算关键特性说明
description: Mmad计算关键特性集合，涵盖GEMV、HF32、UnitFlag及K方向对齐约束等特性说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/mmad_compute_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Mmad计算关键特性说明

Mmad 矩阵乘计算的关键特性说明集合，涵盖 GEMV（矩阵向量乘）、HF32（半精度浮点格式）、UnitFlag（单位标志控制）以及 K 方向对齐约束。这些特性影响 Mmad 接口的精度选择、数据格式与对齐要求，使用前需确认目标硬件与场景是否支持对应特性，并遵循各特性的数据布局与对齐约束。
