---
type: API
title: SIMD计算说明
description: SIMD计算说明集合，涵盖概述、连续计算、高维切分和掩码等主题。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/SIMD_compute/SIMD_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SIMD计算说明

矢量计算通过 Vector 计算单元完成，源操作数和目的操作数均通过 Unified Buffer（UB）存储。提供连续计算和高维切分两种计算模式，并可通过掩码（Mask）实现数据选择性参与计算。

连续计算简单直观，适合一维 Tensor 连续数据处理；高维切分计算灵活可控，支持迭代执行和地址间隔配置，适合多维数据处理。开发者可根据实际业务需求选择合适的计算方式。
