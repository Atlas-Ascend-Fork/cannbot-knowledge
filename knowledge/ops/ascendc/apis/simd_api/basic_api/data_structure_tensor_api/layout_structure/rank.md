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

<!-- cannbot:related:start -->
## 相关

- [低 rank 零填充致 count=0 用 td_->rank 非 RANK](../../../../../runbooks/precision/rank_count_0_td_rank_rank.md)（`exemplifies`）：低 rank 零填充致 count=0 用 td_->rank 非 RANK 与《基础APIRank》的实质衔接是：实际 rank 必须来自 tiling 而非模板容量；低 rank padding、NDDMA维度、shape/axes 和 blockDim 卡共同验证零填充维被误纳入循环后 count=0 的机制。
- [Layout](layout.md)（`related`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《基础APIRank》补充：用于返回Layout的秩。
- [GetShape](get_shape.md)（`same_topic`）：基础APIRank 与《GetShape》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [Layout和层次化表述法](layout_hierarchical_representation.md)（`same_topic`）：基础APIRank 与《Layout和层次化表述法》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [MakeLayout](make_layout.md)（`same_topic`）：基础APIRank 与《MakeLayout》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [Shape（基础API）](shape.md)（`same_topic`）：基础APIRank 与《Shape（基础API）》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [Stride（基础API）](stride.md)（`same_topic`）：基础APIRank 与《Stride（基础API）》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《基础APIRank》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
