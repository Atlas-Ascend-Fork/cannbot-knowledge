---
type: API
title: K方向对齐约束
description: Atlas A2 训练系列产品/Atlas A2 推理系列产品/Atlas A3 训练系列产品/Atlas A3 推理系列产品，Mmad接口支持开启此特性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute_key_features/k_direction_alignment_constraint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# K方向对齐约束

通过 MmadParams.kDirectionAlign 控制 float 数据类型时 L0A/L0B Buffer 矩阵 K 方向对齐方式。true 对齐到 ceil(K/16)×16，false 对齐到 ceil(K/8)×8。A 矩阵非转置场景无需开启；转置场景需开启以避免读入无效数据。950 的 L0A Buffer 为 NZ 排布，K 方向 8 对齐，无需此特性。仅 a2/a3 支持。
