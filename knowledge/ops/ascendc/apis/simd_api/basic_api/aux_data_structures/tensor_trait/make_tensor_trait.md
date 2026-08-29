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

- [is_tensorTrait](is_tensor_trait.md)（`related`）：典型用法：先通过 MakeTensorTrait 构造 TensorTrait 对象，再使用 is_tensorTrait<decltype(obj)>::value 验证；对 Shape、Stride、Layout 等非 TensorTrait 类型，value 为 false。；构造TensorTrait结构体的辅助函数。通过传入TensorDesc和Layout等信息创建TensorTrait。函数原型提供多种重载，支持不同的参数组合。返回TensorTrait结构体。用于快速创建包含Layout信息的Tensor特性描述。；MakeTensorTrait 产生 TensorTrait 对象，is_tensorTrait 随后对该对象类型做编译期识别，正文给出直接的构造—验证用法。
<!-- cannbot:related:end -->
