---
type: API
title: 矩阵计算的搬出总体说明
description: 矩阵计算的搬出接口主要实现L0C Buffer与Global Memory、Unified Buffer之间的数据高效传输。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_store/overall_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Cube Store总体说明

Cube计算Store操作通过统一Copy接口将L0C Buffer计算结果搬运到GM或UB。支持连续搬出、格式转换、Batch搬出、随路量化/ReLU、F32通道切分、INT8通道合并、双目的搬出等场景。
