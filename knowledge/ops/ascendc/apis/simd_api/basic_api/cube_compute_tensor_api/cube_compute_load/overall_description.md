---
type: API
title: 矩阵计算的搬入总体说明
description: 矩阵计算的搬入接口主要实现Global Memory到L1 Buffer和L1 Buffer到L0A Buffer/L0B Buffer/L0ScaleA
  Buffer/L0ScaleB Buffer/BiasTable Buffer/Fixpipe Buffer的数据高效传输。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/overall_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Cube Load总体说明

Cube计算Load操作通过统一Copy接口实现不同存储层次间的数据搬运，搬运参数由Tensor Layout自动推导。支持GM到L1、L1到L0A/L0B/L0ScaleA/L0ScaleB/BiasTable/Fixpipe等通路。

各通路支持的数据格式转换场景因源/目的位置和数据类型而异，包括连续搬运、格式转换（ND/NZ/ZN/Fractal等）、Batch多矩阵搬运、Scale数据搬运、卷积特征图搬运等。
