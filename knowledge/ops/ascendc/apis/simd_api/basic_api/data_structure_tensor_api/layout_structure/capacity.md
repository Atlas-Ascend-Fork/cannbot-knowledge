---
type: API
title: Capacity（基础API）
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Capacity用于计算Layout所需的实际内存容量。
  与Size（有效元素个数）不同，Capacity包含了因非连续步长导致的无效数据区域。对于连续排列（stride紧凑），Capacity与Size相等；对于有间隔的排列，Capacity通常大于Size。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Capacity.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Capacity（基础API）

计算 Layout 所需的实际内存容量，包含因非连续步长导致的无效数据区域。连续排列时 Capacity 与 Size 相等，有间隔时 Capacity 通常大于 Size。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [基础APISize](size.md)（`related`）：“返回 Layout 的有效元素个数，不包含因非连续步长导致的无效数据区域。头文件为 tensor_api/tensor.h。”与“计算 Layout 所需的实际内存容量，包含因非连续步长导致的无效数据区域。连续排列时 Capacity 与 Size 相等，有间隔时 Capacity 通常大于 Size。头文件 `tensor_api/tensor.h`。仅 950 支持。”。Size 统计有效元素，Capacity 包含非连续步长空洞，二者给出逻辑计数与实际容量边界。
<!-- cannbot:related:end -->
