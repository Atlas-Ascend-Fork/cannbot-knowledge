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
