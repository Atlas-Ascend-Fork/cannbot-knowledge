---
type: API
title: 基础APISize
description: 返回 Layout 的有效元素数量，并支持通过模板索引选择要统计的维度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Size.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 基础APISize

返回 Layout 的有效元素个数，不包含因非连续步长导致的无效数据区域。头文件为 tensor_api/tensor.h。
函数签名为 template <size_t... Is, typename Shape, typename Stride> auto Size(const Layout<Shape, Stride>& layout)，通过模板参数 Is 指定要统计的维度。
返回值为 Layout 的有效元素个数，连续排列时与 Capacity 相等。
约束：索引 Is 必须在有效维度范围内。
本接口为试验接口，后续版本可能调整，不保证兼容性。仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Capacity（基础API）](capacity.md)（`related`）：“返回 Layout 的有效元素个数，不包含因非连续步长导致的无效数据区域。头文件为 tensor_api/tensor.h。”与“计算 Layout 所需的实际内存容量，包含因非连续步长导致的无效数据区域。连续排列时 Capacity 与 Size 相等，有间隔时 Capacity 通常大于 Size。头文件 `tensor_api/tensor.h`。仅 950 支持。”。Size 统计有效元素，Capacity 包含非连续步长空洞，二者给出逻辑计数与实际容量边界。
<!-- cannbot:related:end -->
