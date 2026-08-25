---
type: API
title: 矩阵计算的搬出
description: 矩阵计算 TensorAPI 搬出接口集，涵盖 L0C 到 GM、L0C 到 UB 的 Copy 接口及 L0C Buffer 内存结构。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_store/cube_compute_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 矩阵计算的搬出

矩阵计算 TensorAPI 搬出接口集，提供 L0C Buffer 计算结果向外部存储搬运的接口。
包含 L0C Buffer 内存结构介绍，以及 Copy 接口支持 L0C 到 Global Memory 和 L0C 到 Unified Buffer 两种搬运路径。
搬出过程可配合随路量化、随路 ReLU 等后处理特性，具体参见矩阵搬出关键特性说明。
