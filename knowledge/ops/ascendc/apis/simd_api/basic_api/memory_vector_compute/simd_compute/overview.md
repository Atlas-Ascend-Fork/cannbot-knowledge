---
type: API
title: SIMD计算概述
description: 矢量计算通过Vector计算单元完成，矢量计算的源操作数和目的操作数均通过Unified Buffer（UB）来进行存储。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

矢量计算通过Vector计算单元完成，矢量计算的源操作数和目的操作数均通过Unified Buffer（UB）来进行存储。

Memory矢量计算提供连续计算和高维切分两种计算模式，并可通过掩码实现数据选择性参与计算。

以Add接口为例，两种计算模式的调用方式示意图如下。其中，连续计算简单直观，适合一维Tensor连续数据处理；高维切分计算灵活可控，支持迭代执行和地址间隔配置。开发者可根据实际业务需求选择合适的计算方式。

<!-- cannbot:related:start -->
## 相关

- [SIMD算子实现概述](../../../../../guides/operator_practice/simd_operator_impl/vector_programming/overview.md)（`explains`）：焦点处理SIMD 算子实现总览中的双缓冲和计算模型；SIMD计算概述正文界定“矢量计算通过Vector计算单元完成，矢量计算的源操作数和目的操作数均通过Unified Buffer（UB）来进行存储”。候选只保留与总览正文直接展开的 SIMD 计算、DoubleBuffer 机制及其重复说明。
<!-- cannbot:related:end -->
