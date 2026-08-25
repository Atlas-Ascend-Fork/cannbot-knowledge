---
type: API
title: TensorDesc简介
description: TensorDesc用于储存ListTensorDesc.GetDesc\(\)中根据index获取对应的Tensor描述信息。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/TensorDesc_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# TensorDesc简介

TensorDesc是Tensor描述符，用于描述Tensor的元信息，包括shape（形状）、data type（数据类型）、layout（排布）和地址等。TensorDesc提供GetShape、GetDim、GetDataPtr等接口查询Tensor属性，也提供SetShapeAddr等接口修改Tensor信息。常与ListTensorDesc配合管理多个Tensor。

<!-- cannbot:related:start -->
## 相关

- [如何开发动态输入算子](../../../../../guides/programming_guide/appendix/common_operations/develop_dynamic_input_operator.md)（`explains`）：如何开发动态输入算子 与《TensorDesc简介》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：Crd2Idx 与《TensorDesc简介》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [ListTensorDesc](../list_tensor_desc.md)（`related`）：TensorDesc 介绍明确说明其与 ListTensorDesc 配合并通过索引取得，给出容器与元素的接口关系。
- [GetDataPtr](get_data_ptr.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；TensorDesc简介正文说明“TensorDesc用于储存ListTensorDesc.GetDesc\(\)中根据index获取对应的Tensor描述信息”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
- [TensorDesc](tensor_desc.md)（`same_topic`）：TensorDesc简介：TensorDesc 是 ListTensorDesc 返回的单项描述符；结构卡定义对象，而列表卡定义获取与管理它的上游契约。 目标卡《TensorDesc》补充：TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。
<!-- cannbot:related:end -->
