---
type: API
title: 矩阵计算
description: 汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/cube_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算

汇总Ascend C SIMD高阶API中的矩阵(Cube)计算接口，包含Matmul的Kernel侧接口、Tiling类及计算所需空间查询接口。

本接口组包含 Matmul Kernel侧接口, Matmul Tiling类, 获取Matmul计算所需空间。

本接口属于 Cube 矩阵计算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
