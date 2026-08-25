---
type: API
title: GetDim
description: 获取Tensor的维度。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetDim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# GetDim

获取TensorDesc指定维度的大小。函数原型：uint32_t GetDim(uint32_t dimIdx) const。参数：dimIdx为维度索引。返回指定维度的大小。用于查询Tensor的各维度大小。

<!-- cannbot:related:start -->
## 相关

- [GetShape](get_shape.md)（`related`）：“GetShape”定义：获取对应维度的shape信息。；“GetDim”定义：获取Tensor的维度。。实质衔接：ListTensorDesc 取出 TensorDesc 后，必须先有 shape 地址才能按维读取 GetShape/GetDim；它与编译期 Layout.GetShape 不是同一个对象契约。
- [SetShapeAddr](set_shape_addr.md)（`related`）：SetShapeAddr 写入 TensorDesc 的 shape 存储，GetDim 随后读取该元信息形成写后验证链。
- [构造和析构函数](constructor_and_destructor.md)（`related`）：构造 TensorDesc 写入 shape 后，GetDim 用于读取其维数，形成创建后校验元信息的最短链路。
<!-- cannbot:related:end -->
