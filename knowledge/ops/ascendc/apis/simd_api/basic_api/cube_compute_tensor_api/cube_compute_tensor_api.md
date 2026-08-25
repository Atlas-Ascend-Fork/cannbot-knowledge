---
type: API
title: 矩阵计算（TensorAPI，试验特性）
description: AscendC 矩阵计算 TensorAPI（试验特性）接口总览，涵盖搬入、Mmad 计算、搬出及关键特性说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_TensorAPI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算（TensorAPI，试验特性）

Ascend C 矩阵计算 TensorAPI 导航页（试验特性），提供基于 Tensor 抽象的矩阵计算接口总览。
涵盖矩阵搬入（LoadData/DataCopy）、Mmad 矩阵乘计算、矩阵搬出（Copy）三个阶段，以及 Mmad 计算关键特性、辅助配置和搬出关键特性说明。
TensorAPI 相较 ISASI 接口提供更高层级的 Tensor 抽象，简化矩阵计算的编程复杂度。
