---
type: API
title: GetStride
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分：
  - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/GetStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GetStride

从 Layout 中提取 Stride 部分。不指定模板参数返回完整 Stride 元组；指定 Is... 从顶层 tuple 选择对应索引元素。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [GetStride](../../aux_data_structures/layout/get_stride.md)（`related`）：GetStride说明返回描述内存访问步长的Stride对象，与Shape的维度信息一一对应。
- [Layout](layout.md)（`related`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《GetStride》补充：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分： - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [基础APIGet](get.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“GetStride”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分： - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
- [GetShape](get_shape.md)（`same_topic`）：GetShape 与 GetStride 分别提取 Layout 的逻辑维度和映射步长，二者共同决定坐标到索引。
- [MakeLayout](make_layout.md)（`same_topic`）：GetStride说明需要包含的头文件为：#include "tensor_api/tensor.h"。 GetStride用于从Layout中提取Stride部分： - 不指定模板参数Is...：返回完整的Stride元组。 - 指定模板参数Is...：从Stride顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [MakeStride](make_stride.md)（`same_topic`）：MakeStride说明构造Stride对象，用于描述各维度在内存中的步长。支持传入多个步长值，也支持传入嵌套的Stride子结构以构造层次化Stride。
- [Stride（基础API）](stride.md)（`same_topic`）：Stride（基础API）说明定义张量各维度相邻元素的内存步长，并与 Shape 组合形成 Layout。
- [ViewEngine](../tensor_structure/view_engine.md)（`same_topic`）：ViewEngine 与《GetStride》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《GetStride》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
