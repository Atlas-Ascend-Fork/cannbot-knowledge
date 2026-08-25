---
type: API
title: 基础APIGEMV
description: GEMV的核心功能体现为：当矩阵A的维度M取值为1时，接口可以手动启用GEMV功能，该操作退化为1×K维度的行向量与K×N维度矩阵之间的乘法运算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/mmad_compute_key_features/GEMV.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# GEMV（矩阵向量乘）

GEMV是矩阵-向量乘法的特殊优化模式，当矩阵B或A的某一维度为1时启用。通过特殊的搬运和计算策略，减少不必要的数据搬运和计算开销，提升GEMV场景性能。

GEMV模式通过Mmad接口的模板参数或Tiling配置自动识别和启用。支持half/float等数据类型。
