---
type: API
title: GetDataPtr
description: 获取储存Tensor数据地址。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/GetDataPtr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# GetDataPtr

获取储存Tensor数据地址。

获取储存Tensor数据地址。

本接口属于 Tensor 数据结构操作接口。

返回值：返回储存Tensor数据地址。T数据类型。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core。

<!-- cannbot:related:start -->
## 相关

- [GetDataObj](get_data_obj.md)（`same_topic`）：GetDataPtr 返回 TensorDesc 的裸数据地址，GetDataObj 用同一地址构造 GlobalTensor 访问对象；两者围绕同一 TensorDesc 地址载体提供裸指针与张量封装两种访问合同。
- [ListTensorDesc](../list_tensor_desc.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；ListTensorDesc正文说明“ListTensorDesc用来解析符合以下内存排布格式的数据，并在kernel侧根据索引获取储存对应数据的地址及shape信息。 !”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
- [TensorDesc](tensor_desc.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；TensorDesc正文说明“TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
- [TensorDesc简介](tensor_desc_intro.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；TensorDesc简介正文说明“TensorDesc用于储存ListTensorDesc.GetDesc\(\)中根据index获取对应的Tensor描述信息”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
- [构造和析构函数](constructor_and_destructor.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；构造和析构函数正文说明“创建与释放TensorDesc对象”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
<!-- cannbot:related:end -->
