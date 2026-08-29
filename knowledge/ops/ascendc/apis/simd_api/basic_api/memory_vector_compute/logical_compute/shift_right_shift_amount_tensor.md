---
type: API
title: ShiftRight
description: 对源操作数中的每个元素进行右移操作，右移位数由Tensor指定，无符号类型执行逻辑右移，有符号类型执行算术右移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/ShiftRight_shift_amount_tensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShiftRight

对源操作数中的每个元素进行右移操作，右移位数由Tensor指定，无符号类型执行逻辑右移，有符号类型执行算术右移。

本接口组包含 LocalTensor, LocalTensor。

本接口属于 UB 矢量计算逻辑运算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ShiftRight](shift_right.md)（`related`）：焦点卡写明“右移位数由标量scalarValue决定”，候选卡写明“右移位数由Tensor指定”。两卡分别定义统一标量位移与逐元素 Tensor 位移，形成重载选型。
<!-- cannbot:related:end -->
