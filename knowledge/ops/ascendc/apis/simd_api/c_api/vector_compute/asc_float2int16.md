---
type: API
title: AscFloat2int16
description: 将float类型数据转换为int16_t类型，支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入。 - ROUND舍入模式：四舍五入舍入。
  - FLOOR舍入模式：向负无穷舍入。 - CEIL舍入模式：向正无穷舍入。 - TRUNC舍入模式：向零舍入。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscFloat2int16

将float类型数据转换为int16_t类型，支持多种舍入模式：
函数原型：void asc_float2int16_rn(__ubuf__ int16_t* dst, __ubuf__ float* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2int32](asc_float2int32.md)（`related`）：目标 int32 范围不同，按输出 dtype 选择。
- [AscHalf2int16](asc_half2int16.md)（`related`）：half 源版本精度/范围不同。
- [AscFloat2Int16](../reg/data_type_convert/asc_float2int16.md)（`same_topic`）：《AscFloat2Int16》处理“将float类型数据转化为int16_t类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式与饱和模式。 由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。”。《AscFloat2int16》明确提供“将float类型数据转换为int16_t类型，支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入。 - ROUND舍入模式：四舍五入舍入。 - FLOOR舍入模式：向负无穷舍入。 - CEIL舍入模式：向正无穷舍入。 - TRUNC舍入模式：向零舍入。”，其参数、调用或验证步骤直接接入float 到 int16 的同源同目标转换及 rounding/saturation 选择。
- [AscFloat2Int32](../scalar_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2int16》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
<!-- cannbot:related:end -->
