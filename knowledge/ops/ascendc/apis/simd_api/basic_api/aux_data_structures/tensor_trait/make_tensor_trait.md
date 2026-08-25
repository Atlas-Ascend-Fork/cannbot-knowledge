---
type: API
title: MakeTensorTrait
description: 生成TensorTrait实例化对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/MakeTensorTrait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# MakeTensorTrait

构造TensorTrait结构体的辅助函数。通过传入TensorDesc和Layout等信息创建TensorTrait。函数原型提供多种重载，支持不同的参数组合。返回TensorTrait结构体。用于快速创建包含Layout信息的Tensor特性描述。

<!-- cannbot:related:start -->
## 相关

- [GetLayout](get_layout.md)（`related`）：MakeTensorTrait 从 Layout 生成 TensorTrait 实例，随后可通过 GetLayout 取回布局，连接构造与查询阶段。
- [MakeLayout](../layout/make_layout.md)（`related`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《MakeLayout》补充：将传入的Shape和Stride数据打包成Layout数据结构。
- [TensorDesc](../tensor_desc/tensor_desc.md)（`related`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorDesc》补充：TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。
- [辅助数据结构更多样例](more_examples.md)（`related`）：样例中的 TensorTrait 实例由 MakeTensorTrait 从 Layout 生成，是示例调用成立的构造前提。
- [SetLayout](set_layout.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《SetLayout》补充：设置Layout对象至TensorTrait结构中。
- [TensorTrait](tensor_trait.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorTrait》补充：TensorTrait 辅助数据结构用于承载张量布局信息，提供 GetLayout、SetLayout、MakeTensorTrait 等接口。
- [TensorTrait构造函数](tensor_trait_constructor.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorTrait构造函数》补充：根据输入的Layout对象，实例化TensorTrait对象。
- [TensorTrait简介](tensor_trait_intro.md)（`same_topic`）：MakeTensorTrait：MakeTensorTrait直接以 TensorDesc和Layout构造 TensorTrait；构造/GetLayout/SetLayout卡定义对象后续读写，能核对传入描述符与布局是否保持一致。 目标卡《TensorTrait简介》补充：TensorTrait数据结构是描述Tensor相关信息的基础模板类，包含Tensor的数据类型、逻辑位置和Layout内存布局。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
- [is_tensorTrait](is_tensor_trait.md)（`same_topic`）：MakeTensorTrait说明生成TensorTrait实例化对象。
<!-- cannbot:related:end -->
