---
type: API
title: 关键分形格式详解
description: 矩阵分形存储格式是对多维Tensor在内存中数据排布格式的描述。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/key_fractal_format_details.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Cube Fractal格式关键说明

描述Cube计算中的关键Fractal数据排布格式，包括L0A/L0B的矩阵分块格式（Fractal）和L0C的结果分块格式。Fractal格式将大矩阵切分为固定大小的分块（如16x16），按特定顺序排布在Buffer中，以匹配Cube计算单元的硬件并行处理能力。
