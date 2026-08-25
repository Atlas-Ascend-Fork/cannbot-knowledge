---
type: API
title: AscAddRelu
description: 按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_add_relu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscAddRelu

按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。计算公式如下：
函数原型：void asc_add_relu(__ubuf__ half* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AddDeqRelu](../../basic_api/memory_vector_compute/composite_compute/add_deq_relu.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《AscAddRelu》明确“按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [AddRelu](../../basic_api/memory_vector_compute/composite_compute/add_relu.md)（`related`）：两接口都逐元素 Add 后 ReLU；基础 API 版本以 LocalTensor 表达同一复合计算。
- [AddReluCast](../../basic_api/memory_vector_compute/composite_compute/add_relu_cast.md)（`related`）：当输出 dtype 与输入不同，AddReluCast 显式承载转换；它解释 AscAddRelu 签名中 s16→s8、f32→f16 等随路转换边界。
- [AscMulAddRelu](asc_mul_add_relu.md)（`related`）：AscMulAddRelu 与《AscAddRelu》的实质衔接是：AscMulAddRelu 融合 dst*src0+src1 与 ReLU；MulAdd/AddRelu 对应入口拆解同一计算，FMA 舍入卡和随路量化+ReLU材料给出精度与融合边界。
- [AscRelu](asc_relu.md)（`related`）：AscAddRelu 把加法和 ReLU 融合，适用于 ReLU 前正好需要逐元素加法的路径。
- [AscAdd](asc_add.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAddRelu》补充：按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。
<!-- cannbot:related:end -->
