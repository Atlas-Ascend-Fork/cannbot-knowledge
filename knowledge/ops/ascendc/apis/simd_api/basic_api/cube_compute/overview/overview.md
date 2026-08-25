---
type: API
title: 概述
description: 矩阵计算概述，涵盖矩阵计算单元与矩阵计算流程的导览。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/overview/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

Cube 计算单元专用于执行矩阵运算，直接访问的专用缓存包括：L0A Buffer（存储左矩阵）、L0B Buffer（存储右矩阵）、L0C Buffer（存储累加初值和计算结果）。

矩阵计算关联的存储单元还包括 L1 Buffer（缓存输入数据，从 GM 搬入后分别送往 L0A/L0B）、Fixpipe Buffer（存储量化参数等 Fixpipe 搬运数据）和 BiasTable Buffer（存储矩阵计算的 Bias 偏置数据）。数据流向通常为 GM → L1 → L0A/L0B → L0C → GM/UB。
