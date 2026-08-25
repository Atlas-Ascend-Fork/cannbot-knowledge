---
type: API
title: AscFloat2int64
description: 将float类型转化为int64_t类型，并支持多种舍入模式： * RINT舍入模式：四舍六入五成双舍入 * ROUND舍入模式：四舍五入舍入
  * FLOOR舍入模式：向负无穷舍入 * CEIL舍入模式：向正无穷舍入 * TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2int64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscFloat2int64

将float类型转化为int64_t类型，并支持多种舍入模式： RINT舍入模式：四舍六入五成双舍入 ROUND舍入模式：四舍五入舍入
函数原型：void asc_float2int64_rn(__ubuf__ int64_t* dst, __ubuf__ float* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int32](../scalar_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2int64》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscFloat2Int64](../reg/data_type_convert/asc_float2int64.md)（`same_topic`）：两者都完成 float→int64 并支持舍入选择；Reg 版本增加显式 RegTensor、mask、饱和和高低 lane 控制，可用于迁移计算路径。
<!-- cannbot:related:end -->
