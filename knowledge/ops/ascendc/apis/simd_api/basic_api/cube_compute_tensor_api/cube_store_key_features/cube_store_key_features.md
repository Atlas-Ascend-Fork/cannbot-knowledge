---
type: API
title: 矩阵搬出关键特性说明
description: 矩阵搬出关键特性说明，包含随路量化、随路 Relu、F32 Channel Split、Int8 Channel Merge、batch 搬运等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/cube_store_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬出关键特性说明

矩阵计算 TensorAPI 搬出阶段支持的关键后处理特性，在 L0C 到 GM/UB 搬运过程中随路完成。
包含随路量化（Quant）与随路 ReLU 激活，支持在搬出时同时完成精度转换与激活计算，减少额外计算开销。
F32 Channel Split 和 Int8 Channel Merge 分别支持浮点通道拆分与整型通道合并，batch 搬运支持多 batch 数据的一次性搬出。
L0C Buffer 到 Unified Buffer 双目标模式支持同时向 UB 搬运数据，适配特定计算场景。
