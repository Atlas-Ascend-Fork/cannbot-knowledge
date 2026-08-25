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

- [LeakyRelu](../../basic_api/reg_vector_compute/basic_arithmetic/leaky_relu.md)（`related`）：LeakyRelu 与《AscLeakyrelu》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [AscLeakyrelu](../reg/arithmetic_compute/asc_leakyrelu.md)（`same_topic`）：Vector AscLeakyrelu 与 Reg AscLeakyrelu 执行相同负半轴乘 slope 的激活，可按 UB 与寄存器数据路径选择。
- [LeakyRelu](../../basic_api/memory_vector_compute/basic_arithmetic/leaky_relu.md)（`same_topic`）：LeakyRelu 与《AscLeakyrelu》的实质衔接是：LeakyRelu 的负分支乘 alpha、非负分支保留原值，可由 Muls 与 Maxs/Mins 组合；Prelu、Relu 及 C/Reg 入口给出相同或退化调用语义。
<!-- cannbot:related:end -->
