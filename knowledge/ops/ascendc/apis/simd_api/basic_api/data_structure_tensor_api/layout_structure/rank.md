---
type: API
title: 基础APIRank
description: 用于返回Layout的秩。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Rank.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 基础APIRank

用于返回Layout的秩。

本接口属于 Tensor 数据结构操作接口，用于描述和操作张量的布局与结构。

参数说明：Shape：输入 组成Layout的shape的类型，即元组（tuple）类型。；Stride：输入 组成Layout的stride的类型，即元组（tuple）类型。；Is...：size_t 索引序列，用于编译时递归选择shape和stride的子结构。；layout：输入 Layout用于描述张量的布局。

返回值：返回Layout的秩，即返回Layout布局的Shape或其子结构的元组（tuple）维度的个数。
