---
type: API
title: TensorTrait构造函数
description: 根据输入的Layout对象，实例化TensorTrait对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/TensorTrait_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# TensorTrait构造函数

TensorTrait提供多种构造方式：默认构造、通过TensorDesc和Layout构造、拷贝构造等。构造参数可包含TensorDesc信息、Layout信息等。构造的TensorTrait用于描述Tensor的完整信息（含排布），传递给高阶API使用。

<!-- cannbot:related:start -->
## 相关

- [GetLayout](get_layout.md)（`related`）：构造时写入的 Layout 正是 GetLayout 返回的排布信息，形成创建 TensorTrait 后验证/消费 layout 的直接链路。
- [辅助数据结构更多样例](more_examples.md)（`related`）：构造函数提供直接从 Layout 实例化 TensorTrait 的另一入口，解释样例中编译期布局如何进入算术 API。
- [MakeTensorTrait](make_tensor_trait.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorTrait构造函数》补充：根据输入的Layout对象，实例化TensorTrait对象。
- [TensorTrait](tensor_trait.md)（`same_topic`）：TensorTrait 与《TensorTrait构造函数》的衔接是：TensorTrait 的构造、Make、is、Get 和 Set 是同一 Layout trait 对象的创建、识别与访问契约；缺任一步都会影响 Shape/Stride 布局元数据的传递。
- [is_tensorTrait](is_tensor_trait.md)（`same_topic`）：TensorTrait构造函数说明根据输入的Layout对象，实例化TensorTrait对象。
<!-- cannbot:related:end -->
