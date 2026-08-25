---
type: API
title: AscHalf2int32
description: 将half类型转化为int32_t类型，并支持多种舍入模式： * RINT舍入模式：四舍六入五成双舍入 * ROUND舍入模式：四舍五入舍入
  * FLOOR舍入模式：向负无穷舍入 * CEIL舍入模式：向正无穷舍入 * TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_half2int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscHalf2int32

将half类型转化为int32_t类型，并支持多种舍入模式： RINT舍入模式：四舍六入五成双舍入 ROUND舍入模式：四舍五入舍入
函数原型：void asc_half2int32_rn(__ubuf__ int32_t* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscHalf2Int32](../reg/data_type_convert/asc_half2int32.md)（`related`）：两者都完成 half→int32 并支持 RINT/ROUND/FLOOR/CEIL/TRUNC；Reg 版在寄存器中按 1:2 lane 布局输出，Vector 版在 UB 内存上要求 32B 对齐。
- [__half2int_rd](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_rd.md)（`related`）：__half2int_rd 与《AscHalf2int32》的实质衔接是：这些卡保持 half 到整数转换并切换 rd/rn/rna/ru/rz 或目标有无符号；C 的 half2int16/32 入口说明向量执行层的目标位宽选择。
- [AscFloat2Int32](../scalar_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscHalf2int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [__half2int_ru](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_half2int_ru.md)（`same_topic`）：__half2int_ru 与《AscHalf2int32》的实质衔接是：__half2int_ru 保持 half→int 并切换 rd/rn/rna/rz，或保持 ceil 改变源/目标类型；C half2int16/32 入口明确向量目标位宽。
<!-- cannbot:related:end -->
