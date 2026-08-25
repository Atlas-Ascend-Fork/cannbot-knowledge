---
type: API
title: AscRelu
description: 按元素做线性整流Relu，
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscRelu

按元素做线性整流Relu，计算公式如下：
函数原型：void asc_relu(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscAddRelu](asc_add_relu.md)（`related`）：AscAddRelu 把加法和 ReLU 融合，适用于 ReLU 前正好需要逐元素加法的路径。
- [AscRelu](../reg/arithmetic_compute/asc_relu.md)（`related`）：Reg AscRelu 对寄存器数据执行相同激活，而 Vector AscRelu 直接处理 UB，按数据驻留位置选型。
- [Relu](../../basic_api/memory_vector_compute/basic_arithmetic/relu.md)（`related`）：Basic Memory Relu 是 LocalTensor 风格的对应接口，可用于从 C Vector API 迁移。
- [Relu](../../basic_api/reg_vector_compute/basic_arithmetic/relu.md)（`same_topic`）：焦点处理Reg Relu 的负值清零及跨 API 实现；AscRelu正文界定“按元素做线性整流Relu，”。候选保持 ReLU/PReLU/LeakyReLU 语义或给出同一算子骨架，只改变 API 层或负半轴策略。
<!-- cannbot:related:end -->
