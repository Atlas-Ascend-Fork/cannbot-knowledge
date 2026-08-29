---
type: API
title: 矩阵搬出关键特性说明
description: 矩阵搬出关键特性说明，包含 NZ2ND、Int8 Channel Merge、随路量化、随路 Relu、L0C 到 UB 双目标模式等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_store_key_features/cube_store_key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬出关键特性说明

矩阵计算 ISASI 搬出阶段支持的关键后处理特性，在 L0C 到 GM/UB/L1 搬运过程中随路完成。
格式转换方面支持 NZ2ND、NZ2NZ、NZ2DN 等排布格式变换；通道处理方面支持 Int8 Channel Merge 和 F32 Channel Split 通道合并与拆分。
随路计算方面支持随路量化与随路 ReLU，并支持两者场景组合；另支持 L0C 到 UB 双目标模式和卷积格式转换等特性。
