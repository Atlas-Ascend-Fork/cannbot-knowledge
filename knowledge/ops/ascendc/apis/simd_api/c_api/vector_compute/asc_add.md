---
type: API
title: AscAdd
description: asc_add（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscAdd

执行矢量加法运算。计算公式如下：
函数原型：void asc_add(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src0、src1的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Add算子快速入门](../../../../guides/getting_started/quick_start/simd_programming/add_op_quick_start.md)（`explains`）：快速入门的 C 路径明确以 asc_add 处理 UB 中的 x/y 并输出 z；目标卡补充 UB 指针/count 和 32B 对齐约束。
- [AscAdd](../reg/arithmetic_compute/asc_add.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAdd》补充：根据mask对源操作数src0、src1按元素求和，将结果写入目的操作数dst。可选保留进位到carry寄存器。
- [AscAddRelu](asc_add_relu.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAddRelu》补充：按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。
- [AscAddScalar](../reg/arithmetic_compute/asc_add_scalar.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAddScalar》补充：执行矢量和标量的加法运算，将结果写入目的操作数dst。
- [AscAddScalar](asc_add_scalar.md)（`same_topic`）：AscAdd：Reg AscAdd/AscAddScalar和 Vector AscAddRelu/Scalar是同一逐元素加法的寄存器、标量和融合变体，能直接辅助选择正确原型。 目标卡《AscAddScalar》补充：执行矢量与标量的加法运算，支持连续数据计算、高维切分计算和同步计算模式。
<!-- cannbot:related:end -->
