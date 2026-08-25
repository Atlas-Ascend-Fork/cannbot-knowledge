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

- [Capacity（基础API）](capacity.md)（`related`）：基础APISize说明返回 Layout 的有效元素数量，并支持通过模板索引选择要统计的维度；对Capacity（基础API）而言，Capacity 是 Layout 可寻址元素容量，需用 Cosize/Size 的计算口径和 Layout 的 Shape/Stride 定义辨清含 padding 的内存范围。
- [Cosize（基础API）](cosize.md)（`same_topic`）：基础APISize 与《Cosize（基础API）》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [GetShape](get_shape.md)（`same_topic`）：基础APISize 与《GetShape》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [GetStride](get_stride.md)（`same_topic`）：基础APISize 与《GetStride》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [Layout](layout.md)（`same_topic`）：基础APISize 与《Layout》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`same_topic`）：基础APISize 与《Layout和层次化表述法》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [MakeLayout](make_layout.md)（`same_topic`）：基础APISize 与《MakeLayout》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [Shape（基础API）](shape.md)（`same_topic`）：基础APISize 与《Shape（基础API）》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [Stride（基础API）](stride.md)（`same_topic`）：基础APISize 与《Stride（基础API）》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
- [基础APIRank](rank.md)（`same_topic`）：基础APISize 与《基础APIRank》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
