---
type: API
title: GetShape
description: 获取对应维度的shape信息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# GetShape

获取对应维度的shape信息。

获取对应维度的shape信息。

本接口属于 Tensor 数据结构操作接口。

返回值：返回对应维度的shape信息。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core。

<!-- cannbot:related:start -->
## 相关

- [GetDim](get_dim.md)（`related`）：“GetShape”定义：获取对应维度的shape信息。；“GetDim”定义：获取Tensor的维度。。实质衔接：ListTensorDesc 取出 TensorDesc 后，必须先有 shape 地址才能按维读取 GetShape/GetDim；它与编译期 Layout.GetShape 不是同一个对象契约。
- [ListTensorDesc](../list_tensor_desc.md)（`related`）：“GetShape”定义：获取对应维度的shape信息。；“ListTensorDesc”定义：ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !。实质衔接：ListTensorDesc 取出 TensorDesc 后，必须先有 shape 地址才能按维读取 GetShape/GetDim；它与编译期 Layout.GetShape 不是同一个对象契约。
- [TensorDesc](tensor_desc.md)（`related`）：“GetShape”定义：获取对应维度的shape信息。；“TensorDesc”定义：TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。。实质衔接：ListTensorDesc 取出 TensorDesc 后，必须先有 shape 地址才能按维读取 GetShape/GetDim；它与编译期 Layout.GetShape 不是同一个对象契约。
- [SetShapeAddr](set_shape_addr.md)（`same_topic`）：SetShapeAddr 绑定 shape 存储后，GetShape 读取同一 TensorDesc 元信息，可做写后校验。
<!-- cannbot:related:end -->
