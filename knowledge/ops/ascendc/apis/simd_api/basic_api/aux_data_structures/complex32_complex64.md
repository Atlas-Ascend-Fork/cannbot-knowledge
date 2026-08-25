---
type: API
title: complex32/complex64
description: 复数类型定义，complex32 实部虚部为 half、位宽 32 位，complex64 实部虚部为 float、位宽 64 位，仅 Ascend 950PR/950DT 支持。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/complex32-complex64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# complex32与complex64

complex32和complex64为复数数据类型。complex32由两个half组成（实部和虚部各16位），complex64由两个float组成（实部和虚部各32位）。提供构造、获取实部/虚部、设置实部/虚部等操作。

支持通过构造函数直接创建，或通过实部和虚部值组合创建。复数运算需结合对应的复数计算接口使用。

<!-- cannbot:related:start -->
## 相关

- [Add](../reg_vector_compute/basic_arithmetic/add.md)（`related`）：Add 与《complex32/complex64》的实质衔接是：Reg Add 与 C API Add 实现相同逐 lane 加法；complex32/64 是该接口支持复数重载时所需的操作数契约。
- [RegTensor](../reg_vector_compute/register_data_types/reg_tensor.md)（`related`）：complex32/complex64 与《RegTensor》的实质衔接是：complex32/complex64 定义 Reg 复数操作数布局，RegTensor 承载该类型；复数基础概览补充实部虚部与支持边界。
- [辅助数据结构](aux_data_structures.md)（`same_topic`）：complex32/complex64 与《辅助数据结构》的实质衔接是：complex32/complex64 定义 Reg 复数操作数布局，RegTensor 承载该类型；复数基础概览补充实部虚部与支持边界。
<!-- cannbot:related:end -->
