---
type: API
title: L1与BiasTable Buffer数据搬运
description: DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_BiasTable_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1与BiasTable Buffer数据搬运

DataCopy 实现 L1 Buffer 到 BiasTable Buffer 的连续数据搬运，格式和内容保持不变。用于将矩阵计算的 bias 参数从 L1 搬运至 BiasTable Buffer。BiasTable Buffer 地址需 64B 对齐，L1 Buffer 地址需 32B 对齐。
