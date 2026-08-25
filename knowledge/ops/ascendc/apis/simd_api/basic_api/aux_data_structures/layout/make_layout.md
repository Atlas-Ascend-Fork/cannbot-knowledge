---
type: API
title: MakeLayout
description: 将传入的Shape和Stride数据打包成Layout数据结构。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/MakeLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# MakeLayout

构造Layout结构体的辅助函数。通过传入shape、stride和format等信息创建Layout。函数原型提供多种重载，支持不同维度的shape和stride输入。参数包含shape各维度大小、stride各维度步长、format数据格式。返回Layout结构体。用于快速创建Tensor排布描述。

<!-- cannbot:related:start -->
## 相关

- [GetStride](get_stride.md)（`related`）：GetStride 与《MakeLayout》的实质衔接是：GetStride 从 Layout 读取 MakeStride 生成的维度步长，Crd2Idx 以该 stride 映射坐标；NDDMA stride=0 故障和 Layout 说明验证物理寻址边界。
- [MakeShape](make_shape.md)（`related`）：《MakeShape》说明将传入的数据打包成Shape数据结构。；《MakeLayout》说明将传入的Shape和Stride数据打包成Layout数据结构。。二者在MakeShape产生的Shape与Stride、Coordinate共同进入MakeLayout并由Crd2Idx/GetShape/GetStride消费，形成完整Layout索引合同上存在可执行的直接衔接。
- [MakeStride](make_stride.md)（`related`）：MakeStride 生成的步长对象需与 Shape 一起传给 MakeLayout，形成完整内存布局。
- [MakeTensorTrait](../tensor_trait/make_tensor_trait.md)（`related`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《MakeLayout》补充：将传入的Shape和Stride数据打包成Layout数据结构。
- [is_layout](is_layout.md)（`related`）：《is_layout》说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。；《MakeLayout》说明将传入的Shape和Stride数据打包成Layout数据结构。。二者在is_layout用于识别Layout类型，构造、Shape/Stride访问和MakeLayout是其直接类型契约上存在可执行的直接衔接。
- [Crd2Idx](../coordinate/crd2_idx.md)（`same_topic`）：MakeLayout 与《Crd2Idx》的实质衔接是：MakeLayout 将 MakeShape 和 MakeStride 的结果组合为 Layout；直接构造函数是等价构造路径，Crd2Idx 以该 Layout 做坐标到地址映射，Layout 概念卡解释 shape/stride 的内存契约。
- [Layout构造函数](layout_constructor.md)（`same_topic`）：《Layout构造函数》说明根据输入的Shape和Stride对象，实例化Layout对象。；《MakeLayout》说明将传入的Shape和Stride数据打包成Layout数据结构。。二者在Layout由Shape与Stride构造，MakeLayout、GetShape/GetStride、Crd2Idx和is_layout共同定义其类型与索引合同上存在可执行的直接衔接。
- [Layout简介](layout_intro.md)（`same_topic`）：Layout 简介说明 shape、stride 与 format 的抽象，MakeLayout 是据此构造该对象的入口。
- [MakeLayout](../../data_structure_tensor_api/layout_structure/make_layout.md)（`same_topic`）：MakeLayout 与《MakeLayout》的实质衔接是：MakeLayout 将 MakeShape 和 MakeStride 的结果组合为 Layout；直接构造函数是等价构造路径，Crd2Idx 以该 Layout 做坐标到地址映射，Layout 概念卡解释 shape/stride 的内存契约。
- [SetLayout](../tensor_trait/set_layout.md)（`same_topic`）：MakeLayout说明将传入的Shape和Stride数据打包成Layout数据结构。
- [layout](layout1.md)（`same_topic`）：layout 与《MakeLayout》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
<!-- cannbot:related:end -->
