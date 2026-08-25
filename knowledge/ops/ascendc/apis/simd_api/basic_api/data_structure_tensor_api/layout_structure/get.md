---
type: API
title: 基础APIGet
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素；
  2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/Get.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 基础APIGet

提供两类能力：对 Tuple 按位置索引提取元素或逐层提取嵌套元素；对 Layout 分别从 Shape 和 Stride 中提取对应位置的子 tuple 组合为新的子 Layout。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [GetShape](get_shape.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“GetShape”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分： - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
- [GetStride](get_stride.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“GetStride”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分： - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
- [Layout](layout.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“Layout”定义：Layout<Shape, Stride>数据结构是描述多维张量内存布局的基础模板类，通过编译时的形状Shape和步长Stride信息，实现逻辑坐标空间到一维内存地址空间的映射。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
- [Select（基础API）](select.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“Select（基础API）”定义：选择Layout的shape和stride指定维度组成新的layout对象并返回。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
<!-- cannbot:related:end -->
