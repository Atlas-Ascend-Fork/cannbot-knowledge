---
type: API
title: AscLeakyrelu
description: 执行矢量Leaky Relu运算。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_leakyrelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscLeakyrelu

执行矢量Leaky Relu运算。计算公式如下：
函数原型：void asc_leakyrelu(__ubuf__ half* dst, __ubuf__ half* src, half value, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscLeakyrelu](../reg/arithmetic_compute/asc_leakyrelu.md)（`same_topic`）：执行矢量Leaky Relu运算。计算公式如下：；该接口用于按元素执行Leaky ReLU（Leaky Rectified Linear Unit）操作：当源操作数中某元素大于0时，直接将该元素写入目的操作数；否则将该元素乘以标量值value后写入目的操作数。。两卡是同一 C API LeakyReLU 语义的 A2/A3 UB 指针版与 950 寄存器 mask 版。
<!-- cannbot:related:end -->
