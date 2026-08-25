---
type: API
title: 矩阵计算单元（概述）
description: Cube计算单元专用于执行矩阵运算，直接访问的专用缓存如下：L0A Buffer用于存储左矩阵，L0B Buffer用于存储右矩阵，L0C
  Buffer则用于存储初始化累加值和矩阵计算结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/overview/cube_compute_unit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 矩阵计算单元（概述）

Cube 计算单元专用于矩阵运算，直接访问的专用缓存：L0A Buffer 存储左矩阵、L0B Buffer 存储右矩阵、L0C Buffer 存储累加初始化值和计算结果。关联存储单元含 L1 Buffer（输入数据缓存，从 GM 搬入）、Fixpipe Buffer（Fixpipe 量化参数）、BiasTable Buffer（偏置数据）。数据流为 GM→L1→L0A/L0B→（Mmad）→L0C→（Fixpipe）→GM。
