---
type: API
title: AscMin
description: asc_min（矢量计算）
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscMin

按元素求最小值，计算公式如下。
函数原型：void asc_min(__ubuf__ int16_t* dst, __ubuf__ int16_t* src0, __ubuf__ int16_t* src1, uint32_t count)
参数：dst（输出）：目的操作数（矢量）的起始地址。；src0、src1（输入）：源操作数（矢量）的起始地址。；count（输入）：参与计算的元素个数。
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：AscMin 与《Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [Min](../../basic_api/reg_vector_compute/basic_arithmetic/min.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《AscMin》说明asc_min（矢量计算）。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [AscMin](../reg/arithmetic_compute/asc_min.md)（`same_topic`）：AscMin 与《AscMin》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [AscMinScalar](asc_min_scalar.md)（`same_topic`）：AscMin 与《AscMinScalar》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [Min](../../basic_api/memory_vector_compute/basic_arithmetic/min.md)（`same_topic`）：AscMin 与《Min》的实质衔接是：AscMin 是两个同长 UB 向量逐元素取小；Reg/C++ 对应入口和 scalar 变体用于区分 mask/operand 形态，广播故障明确 src1 不能只给一个标量。
- [min（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/min.md)（`same_topic`）：min（整数数学函数） 与《AscMin》的实质衔接是：max 与 min、不同整数宽度/符号重载及 SIMD Min 入口直接对照 focal 模板重载的选择与边界值语义。
<!-- cannbot:related:end -->
