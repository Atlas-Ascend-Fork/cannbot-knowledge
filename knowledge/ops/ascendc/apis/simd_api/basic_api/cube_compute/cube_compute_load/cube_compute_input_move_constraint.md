---
type: API
title: 矩阵计算输入搬运约束
description: 具体可见表数据通路和存储层级。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/cube_compute_input_move_constraint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# Cube计算输入搬运约束

描述Cube计算输入数据搬运的各种约束条件，涵盖GM到L1、L1到L0A/L0B、UB到L1等各通路的地址对齐、数据长度、格式转换、Batch搬运等约束。约束因数据类型、源/目的格式、产品型号而异。

关键约束包括：地址对齐要求（32B/64B等）、数据长度限制、格式转换支持矩阵、Batch搬运条件、Scale数据搬运约束等。开发者在调用LoadData/DataCopy接口前需确认满足相应约束。
