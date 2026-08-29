---
type: API
title: 辅助矩阵分形格式详解
description: 针对Ascend 950PR/Ascend 950DT产品：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_fractal_intro/aux_cube_fractal_format_details.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Cube Fractal格式详细说明（辅助）

详细描述Cube计算中各存储层次的数据Fractal排布格式，包括L1 Buffer的NZ/ZN格式、L0A/L0B的Fractal格式、L0C的Fractal格式等。涵盖各格式在不同数据类型（half/float/int8等）下的具体排布参数（C0、N0、M0等）和地址计算方法。
