---
type: API
title: AscSubRelu
description: 按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_sub_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSubRelu

按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。计算公式如下：
函数原型：void asc_sub_relu(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscSub](../reg/arithmetic_compute/asc_sub.md)（`related`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《AscSubRelu》说明按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [AscSub](asc_sub.md)（`same_topic`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《AscSubRelu》补充：按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。
- [SubRelu](../../basic_api/memory_vector_compute/composite_compute/sub_relu.md)（`same_topic`）：SubRelu 与《AscSubRelu》的实质衔接是：SubRelu 的手工 mask 路径要求先设置 Normal mask，调用后 ResetMask；SubReluCast 和 AscSubRelu 分别补充窄化输出与 C API 对应入口。
- [SubReluCast](../../basic_api/memory_vector_compute/composite_compute/sub_relu_cast.md)（`same_topic`）：AscSubRelu 是 C API 下相同的 Sub→ReLU→类型转换融合链，可直接映射支持的转换组合。
<!-- cannbot:related:end -->
