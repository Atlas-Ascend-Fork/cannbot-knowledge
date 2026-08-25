---
type: API
title: GetShape
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分：
  - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/GetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GetShape

从 Layout 中提取 Shape 部分。不指定模板参数返回完整 Shape 元组；指定 Is... 从顶层 tuple 选择对应索引元素，单个索引返回该元素，多个索引返回新 tuple。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Coshape](coshape.md)（`related`）：GetShape 返回逻辑定义域 shape，Coshape 返回映射后的陪域 shape，二者区分逻辑维度和物理索引范围。
- [Layout](layout.md)（`related`）：Layout：Layout 的 Shape/Stride 映射由 MakeLayout 构造并由层次化表述解释嵌套分形；GetShape/GetStride/Rank是正文点名的核心观察接口。 目标卡《GetShape》补充：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分： - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [基础APIGet](get.md)（`related`）：“基础APIGet”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 Get提供两类能力： 1. 对元组Tuple，按位置索引提取元素或逐层提取嵌套元素； 2. 对Layout，分别从shape和stride中提取对应位置的子tuple，再组合为新的子Layout。；“GetShape”定义：需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分： - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。。实质衔接：Get 从 Tuple 或 Layout 的 shape/stride 同步提取子结构；GetShape/GetStride 和 Select 分别提供整侧提取与维度选择对照。
- [数据结构(TensorAPI，试验特性)](../data_structure_tensor_api.md)（`related`）：GetShape 从 TensorAPI Layout 取出层次 shape，可用于验证 MakeTensor 前后的布局契约。
- [GetStride](get_stride.md)（`same_topic`）：GetShape 与 GetStride 分别提取 Layout 的逻辑维度和映射步长，二者共同决定坐标到索引。
- [MakeLayout](make_layout.md)（`same_topic`）：GetShape说明需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分： - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
- [MakeShape](make_shape.md)（`same_topic`）：MakeShape 构造随后由 GetShape 读取的 Shape 元组，形成创建和查询契约。
- [Shape（基础API）](shape.md)（`same_topic`）：GetShape 从 Layout 读取 Shape，连接布局对象与 shape 查询。
- [ViewEngine](../tensor_structure/view_engine.md)（`same_topic`）：ViewEngine 与《GetShape》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
- [基础APIRank](rank.md)（`same_topic`）：基础APIRank 与《GetShape》的实质衔接是：Rank 返回 Layout 的 Shape/子结构元组层数；MakeLayout、GetShape、Shape/Stride 与层次化 Layout 说明共同界定被计数的对象，而不是运行时 tensor rank。
- [基础APISize](size.md)（`same_topic`）：基础APISize 与《GetShape》的实质衔接是：Size 从 Layout 的 Shape 与 Stride 计算逻辑元素数；Capacity、Cosize、Rank 及层次化表述用于区分逻辑大小、物理跨度和布局构造结果。
<!-- cannbot:related:end -->
