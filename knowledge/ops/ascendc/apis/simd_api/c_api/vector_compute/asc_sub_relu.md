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

- [AscSub](asc_sub.md)（`same_topic`）：执行矢量减法运算；按元素求差，再进行Relu计算。AscSubRelu 在与 AscSub 相同的逐元素减法基础上追加 ReLU 和可选结果类型转换，直接支持在是否需要融合激活时选择接口。
- [SubRelu](../../basic_api/memory_vector_compute/composite_compute/sub_relu.md)（`same_topic`）：“按元素求差，再进行Relu计算（结果和0对比取较大值）。”与“按元素求差，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。计算公式如下：”是双方正文中的具体合同。二者核心都是逐元素差后 ReLU；C API 版本额外提供结果类型转换，互读能判断是否需要融合转换以及对应平台接口。
<!-- cannbot:related:end -->
