---
type: API
title: AscFloat2int32
description: 将float类型转化为int32_t类型，并支持多种舍入模式： * RINT舍入模式：四舍六入五成双舍入 * ROUND舍入模式：四舍五入舍入
  * FLOOR舍入模式：向负无穷舍入 * CEIL舍入模式：向正无穷舍入 * TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscFloat2int32

将float类型转化为int32_t类型，并支持多种舍入模式： RINT舍入模式：四舍六入五成双舍入 ROUND舍入模式：四舍五入舍入
函数原型：void asc_float2int32_rn(__ubuf__ int32_t* dst, __ubuf__ float* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2int16](asc_float2int16.md)（`related`）：目标 int32 范围不同，按输出 dtype 选择。
- [AscFloat2Int32](../reg/data_type_convert/asc_float2int32.md)（`same_topic`）：两张 AscFloat2Int32 卡都执行 float→int32 转换，分别作用于 UB vector 与寄存器向量，并共享舍入模式选择。
- [AscFloat2Int32](../scalar_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [__float2int_rn](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rn.md)（`same_topic`）：__float2int_rn 与《AscFloat2int32》的实质衔接是：__float2int_rn 与 RNA/RD/RU/RZ 共享 float→int32 契约；类型转换总览和 AscFloat2int32/Cast 映射出对应舍入模式与溢出边界。
- [__float2int_rz](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_float2int_rz.md)（`same_topic`）：__float2int_rz 与《AscFloat2int32》的实质衔接是：__float2int_rz 按 CAST_TRUNC 把 float 饱和到 int32；RN/RNA/RD/RU、转换总览、AscFloat2int32 与 Cast/Truncate 映射同一模式。
<!-- cannbot:related:end -->
