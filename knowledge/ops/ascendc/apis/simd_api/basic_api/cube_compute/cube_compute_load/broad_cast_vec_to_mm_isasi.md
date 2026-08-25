---
type: API
title: BroadCastVecToMMISASI
description: 将矢量数据广播到矩阵中，每个数据块中的每16个元素会被连续复制16次；当前支持的数据传输通路：Unified Buffer-\>L0C Buffer（VECIN/VECCALC/VECOUT-\>CO1）。
  图1 功能示例 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/BroadCastVecToMM_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# BroadCastVecToMM

将向量数据广播为矩阵格式后搬入L0A或L0B，用于GEMV（矩阵-向量乘）场景。将1维向量数据沿某一维度复制扩展为2维矩阵排布，避免开发者手动构造矩阵数据。

函数原型通过模板参数指定数据类型和广播方向。参数包含源数据Tensor、目的L0A/L0B Tensor、广播参数等。约束：遵循Cube计算地址对齐约束。
