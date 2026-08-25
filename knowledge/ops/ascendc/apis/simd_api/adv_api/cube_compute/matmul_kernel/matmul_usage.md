---
type: API
title: Matmul使用说明
description: Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Matmul_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Matmul使用说明

Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。 Matmul的计算公式为：C = A * B + Bias，其示意图如下。 - A、B为源操作数，A为左矩阵，形状为[M, K]；B为右矩阵，形状为[K, N]。 - C为目的操作数，存放矩阵乘结果的矩阵，形状为[M, N]。 - Bias为矩阵乘偏置，形状为[1, N]。对A*B结果矩阵的每一行都采用该Bias进行偏置。 图1 Matmul矩阵乘示意图

涵盖以下类别：实现原理。
