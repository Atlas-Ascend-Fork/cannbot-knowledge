---
type: API
title: Select（基础API）
description: 选择Layout的shape和stride指定维度组成新的layout对象并返回。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Select（基础API）

选择 Layout 的 Shape 和 Stride 中指定维度，组成新的子 Layout 对象返回。头文件为 tensor_api/tensor.h。
通过模板参数 Is 指定要保留的维度索引序列，编译时递归选择 shape 和 stride 的子结构。
函数签名为 template <size_t... Is, typename Shape, typename Stride> auto Select(const Layout<Shape, Stride>& layout)，返回子 Layout 对象。
约束：索引 Is 必须在有效维度范围内，否则编译失败。
典型用法：对三维 Layout 调用 Select<0, 1> 可得到由第 0、1 维组成的新 Layout。本接口为试验接口，仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [MakeLayout](make_layout.md)（`related`）：Select 消费一个已有 Layout 并同时抽取其 shape/stride 指定维度；MakeLayout 说明该 Layout 本来由 Shape 和 Stride 组成，是 Select 的直接上游对象构造。
- [Squeeze](squeeze.md)（`related`）：Squeeze 只允许删除大小为 1 的维度且保留 Tensor 存储，Select 则按编译期索引任意保留 Shape/Stride 子维；二者提供维度重写时的约束化选择。
- [基础APIGet](get.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“Select（基础API）”定义：选择Layout的shape和stride指定维度组成新的layout对象并返回。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
<!-- cannbot:related:end -->
