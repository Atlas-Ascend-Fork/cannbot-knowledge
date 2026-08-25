---
type: API
title: BatchCopy
description: L0C Buffer到GM或UB搬运在矩阵最外层增加Batch维度的能力，用于一次完成多块矩阵计算结果的搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/batch_copy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Batch Copy

Batch多矩阵搬运功能，当源/目的Layout带Batch轴时，一次Copy完成多个矩阵的搬运。支持ND2ND、ND2NZ、DN2NZ等多种格式转换场景下的Batch搬运，减少搬运指令数量，提升性能。
