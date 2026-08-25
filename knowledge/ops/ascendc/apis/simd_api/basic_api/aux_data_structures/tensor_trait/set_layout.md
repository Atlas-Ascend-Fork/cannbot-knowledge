---
type: API
title: SetLayout
description: 设置Layout对象至TensorTrait结构中。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/SetLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# SetLayout

设置TensorTrait的Layout信息。函数原型：void SetLayout(const Layout& layout)。参数：layout为待设置的Layout结构体。用于更新Tensor的排布信息。

<!-- cannbot:related:start -->
## 相关

- [GetLayout](get_layout.md)（`same_topic`）：SetLayout 写入 TensorTrait 的 Layout，GetLayout 读取同一对象，形成直接写后查询契约。
- [Layout构造函数](../layout/layout_constructor.md)（`same_topic`）：Layout构造函数说明根据输入的Shape和Stride对象，实例化Layout对象。
- [MakeLayout](../layout/make_layout.md)（`same_topic`）：MakeLayout说明将传入的Shape和Stride数据打包成Layout数据结构。
- [MakeTensorTrait](make_tensor_trait.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《SetLayout》补充：设置Layout对象至TensorTrait结构中。
- [TensorTrait](tensor_trait.md)（`same_topic`）：TensorTrait 与《SetLayout》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
- [TensorTrait简介](tensor_trait_intro.md)（`same_topic`）：SetLayout 生成替换布局后的 trait，连接布局变换与 TensorTrait 的静态类型传播。
- [is_layout](../layout/is_layout.md)（`same_topic`）：is_layout说明判断输入的数据结构是否为Layout数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是Layout类型；反之则为非Layout类型。
- [is_tensorTrait](is_tensor_trait.md)（`same_topic`）：is_tensorTrait说明判断输入的数据结构是否为TensorTrait数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是TensorTrait类型；反之则为非TensorTrait类型。
- [layout](../layout/layout1.md)（`same_topic`）：layout 与《SetLayout》的实质衔接是：Layout 同时承载 shape、stride 与 format，由 MakeLayout 构造并通过 Get/Set 访问；Crd2Idx、排布格式与 NDExtLayout 方向故障验证其寻址语义。
<!-- cannbot:related:end -->
