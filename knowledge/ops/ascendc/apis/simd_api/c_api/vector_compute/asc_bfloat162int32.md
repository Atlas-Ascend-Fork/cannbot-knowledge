---
type: API
title: AscBfloat162int32
description: 将bfloat16_t类型数据转换为int32_t类型，并支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入
  - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_bfloat162int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscBfloat162int32

将bfloat16_t类型数据转换为int32_t类型，并支持多种舍入模式：
函数原型：void asc_bfloat162int32_rn(__ubuf__ int32_t* dst, __ubuf__ bfloat16_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscBfloat162Int32](../reg/data_type_convert/asc_bfloat162int32.md)（`same_topic`）：AscBfloat162int32 与《AscBfloat162Int32》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [AscFloat2Int32](../scalar_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscBfloat162int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [__bfloat162int_rd](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rd.md)（`same_topic`）：AscBfloat162int32 与《__bfloat162int_rd》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [__bfloat162int_rn](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rn.md)（`same_topic`）：AscBfloat162int32 与《__bfloat162int_rn》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [__bfloat162int_rna](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rna.md)（`same_topic`）：AscBfloat162int32 与《__bfloat162int_rna》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [__bfloat162int_ru](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_ru.md)（`same_topic`）：AscBfloat162int32 与《__bfloat162int_ru》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [__bfloat162int_rz](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rz.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《AscBfloat162int32》补充：将bfloat16_t类型数据转换为int32_t类型，并支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
<!-- cannbot:related:end -->
