---
type: API
title: TensorDesc
description: TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/TensorDesc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# TensorDesc

TensorDesc 用于描述张量的形状与数据指针信息，是矢量计算接口中传递张量元数据的辅助数据结构。
提供构造与析构函数管理生命周期，SetShapeAddr 设置形状与数据地址，GetDim/GetIndex/GetShape 查询维度与形状信息，GetDataPtr/GetDataObj 获取数据指针与数据对象。

<!-- cannbot:related:start -->
## 相关

- [如何开发动态输入算子](../../../../../guides/programming_guide/appendix/common_operations/develop_dynamic_input_operator.md)（`explains`）：如何开发动态输入算子 与《TensorDesc》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [Crd2Idx](../coordinate/crd2_idx.md)（`related`）：Crd2Idx 与《TensorDesc》的实质衔接是：Crd2Idx 用 Coordinate 与 Layout 的 shape/stride 计算线性索引，MakeCoord、Layout/TensorDesc 构造和 GetStride 提供两种重载所需的数据结构。
- [GetDataObj](get_data_obj.md)（`related`）：TensorDesc说明TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口；对GetDataObj而言，GetDataObj 返回的对象需按 TensorDesc 的 data pointer 与 index 契约解释，不能把描述对象当作裸数据地址。
- [GetShape](get_shape.md)（`related`）：“GetShape”定义：获取对应维度的shape信息。；“TensorDesc”定义：TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。。实质衔接：ListTensorDesc 取出 TensorDesc 后，必须先有 shape 地址才能按维读取 GetShape/GetDim；它与编译期 Layout.GetShape 不是同一个对象契约。
- [ListTensorDesc](../list_tensor_desc.md)（`related`）：ListTensorDesc 存放并按索引返回 TensorDesc，目标卡定义列表元素本身的 shape、dtype 等描述内容。
- [MakeTensorTrait](../tensor_trait/make_tensor_trait.md)（`related`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorDesc》补充：TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。
- [GetDataPtr](get_data_ptr.md)（`same_topic`）：焦点处理TensorDesc 数据地址读取和 GlobalTensor 包装；TensorDesc正文说明“TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口”。候选说明该裸地址如何由 TensorDesc 取得并封装成可访问的 GlobalTensor。
- [TensorDesc简介](tensor_desc_intro.md)（`same_topic`）：TensorDesc简介：TensorDesc 是 ListTensorDesc 返回的单项描述符；结构卡定义对象，而列表卡定义获取与管理它的上游契约。 目标卡《TensorDesc》补充：TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。
<!-- cannbot:related:end -->
