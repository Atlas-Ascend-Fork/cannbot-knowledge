---
type: API
title: is_tensorTrait
description: 判断输入的数据结构是否为TensorTrait数据结构，可通过检查其成员常量value的值来判断。当value为true时，表示输入的数据结构是TensorTrait类型；反之则为非TensorTrait类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/is_tensorTrait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# is_tensorTrait

判断输入的数据结构是否为 TensorTrait 类型，通过成员常量 value 的值判断：value 为 true 表示是 TensorTrait，反之则不是。
函数签名为 template <typename T> struct is_tensorTrait，模板参数 T 为待判断的数据类型。无返回值，结果通过 value 静态常量获取。
典型用法：先通过 MakeTensorTrait 构造 TensorTrait 对象，再使用 is_tensorTrait<decltype(obj)>::value 验证；对 Shape、Stride、Layout 等非 TensorTrait 类型，value 为 false。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品，Atlas 200I/500 A2 推理产品、Atlas 推理系列产品与 Atlas 训练系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [MakeTensorTrait](make_tensor_trait.md)（`related`）：典型用法：先通过 MakeTensorTrait 构造 TensorTrait 对象，再使用 is_tensorTrait<decltype(obj)>::value 验证；对 Shape、Stride、Layout 等非 TensorTrait 类型，value 为 false。；构造TensorTrait结构体的辅助函数。通过传入TensorDesc和Layout等信息创建TensorTrait。函数原型提供多种重载，支持不同的参数组合。返回TensorTrait结构体。用于快速创建包含Layout信息的Tensor特性描述。；MakeTensorTrait 产生 TensorTrait 对象，is_tensorTrait 随后对该对象类型做编译期识别，正文给出直接的构造—验证用法。
<!-- cannbot:related:end -->
