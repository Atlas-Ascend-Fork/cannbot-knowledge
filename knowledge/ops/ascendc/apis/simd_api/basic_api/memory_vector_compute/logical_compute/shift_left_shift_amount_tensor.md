---
type: API
title: ShiftLeft
description: 对源操作数中的每个元素进行左移操作，左移位数由Tensor指定，无符号类型执行逻辑左移，有符号类型执行算术左移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/ShiftLeft_shift_amount_tensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShiftLeft

对源操作数中的每个元素进行左移操作，左移位数由Tensor指定，无符号类型执行逻辑左移，有符号类型执行算术左移。

本接口组包含 LocalTensor, LocalTensor。

本接口属于 UB 矢量计算逻辑运算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ShiftLeft](shift_left.md)（`same_topic`）：对源操作数中的每个元素进行左移操作，左移位数由标量scalarValue决定，无符号类型执行逻辑左移，有符号类型执行算术左移。；对源操作数中的每个元素进行左移操作，左移位数由Tensor指定，无符号类型执行逻辑左移，有符号类型执行算术左移。。两卡描述相同 ShiftLeft 元素语义的两个重载，核心差异是移位量由单个标量还是逐元素 Tensor 提供。
<!-- cannbot:related:end -->
