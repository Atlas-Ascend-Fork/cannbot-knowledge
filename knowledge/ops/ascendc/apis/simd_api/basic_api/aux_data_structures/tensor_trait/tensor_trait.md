---
type: API
title: TensorTrait
description: TensorTrait 辅助数据结构用于承载张量布局信息，提供 GetLayout、SetLayout、MakeTensorTrait 等接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/TensorTrait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TensorTrait

TensorTrait 用于承载张量的 Layout 布局信息，是矢量计算接口中描述张量排布属性的辅助数据结构。
提供构造函数创建对象，GetLayout/SetLayout 查询与设置布局，MakeTensorTrait 构建布局对象，is_tensorTrait 进行类型判断。

<!-- cannbot:related:start -->
## 相关

- [GetLayout](get_layout.md)（`same_topic`）：TensorTrait 与《GetLayout》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
- [MakeTensorTrait](make_tensor_trait.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorTrait》补充：TensorTrait 辅助数据结构用于承载张量布局信息，提供 GetLayout、SetLayout、MakeTensorTrait 等接口。
- [SetLayout](set_layout.md)（`same_topic`）：TensorTrait 与《SetLayout》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
- [TensorTrait构造函数](tensor_trait_constructor.md)（`same_topic`）：TensorTrait 与《TensorTrait构造函数》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
- [TensorTrait简介](tensor_trait_intro.md)（`same_topic`）：TensorTrait 类型页定义 trait 保存的 dtype 与 Layout，是概念介绍落到类型契约的入口。
- [is_tensorTrait](is_tensor_trait.md)（`same_topic`）：TensorTrait 与《is_tensorTrait》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
<!-- cannbot:related:end -->
