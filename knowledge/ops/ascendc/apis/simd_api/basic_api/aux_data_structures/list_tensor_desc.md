---
type: API
title: ListTensorDesc
description: ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/ListTensorDesc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# ListTensorDesc

ListTensorDesc是Tensor描述符列表，用于管理多个Tensor的描述信息。支持添加、获取和遍历TensorDesc，常用于需要同时处理多个Tensor的场景（如多头注意力等）。

提供构造函数创建空列表，通过AppendTensorDesc添加Tensor描述符，通过GetTensorDesc获取指定位置的描述符，通过GetNum获取列表大小。ListTensorDesc与TBuf配合使用，管理多个LocalTensor的分配。

<!-- cannbot:related:start -->
## 相关

- [如何开发动态输入算子](../../../../guides/programming_guide/appendix/common_operations/develop_dynamic_input_operator.md)（`explains`）：如何开发动态输入算子 与《ListTensorDesc》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [GetShape](tensor_desc/get_shape.md)（`related`）：“GetShape”定义：获取对应维度的shape信息。；“ListTensorDesc”定义：ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !。实质衔接：ListTensorDesc 取出 TensorDesc 后，必须先有 shape 地址才能按维读取 GetShape/GetDim；它与编译期 Layout.GetShape 不是同一个对象契约。
- [TensorDesc](tensor_desc/tensor_desc.md)（`related`）：ListTensorDesc 存放并按索引返回 TensorDesc，目标卡定义列表元素本身的 shape、dtype 等描述内容。
- [TensorDesc简介](tensor_desc/tensor_desc_intro.md)（`related`）：TensorDesc 介绍明确说明其与 ListTensorDesc 配合并通过索引取得，给出容器与元素的接口关系。
- [GetDataPtr](tensor_desc/get_data_ptr.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；ListTensorDesc正文说明“ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
<!-- cannbot:related:end -->
