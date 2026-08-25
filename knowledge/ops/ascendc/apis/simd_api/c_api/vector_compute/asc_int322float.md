---
type: API
title: AscInt322float
description: 将int32_t类型数据转换为float类型，支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入。 - ROUND舍入模式：四舍五入舍入。
  - FLOOR舍入模式：向负无穷舍入。 - CEIL舍入模式：向正无穷舍入。 - TRUNC舍入模式：向零舍入。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int322float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt322float

将int32_t类型数据转换为float类型，支持多种舍入模式：
函数原型：void asc_int322float(__ubuf__ float* dst, __ubuf__ int32_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDeqInt322half](asc_deq_int322half.md)（`related`）：若目标是 fp32 应用 Int32→Float 而非经 half 反量化；目标 dtype 和 scale 需求决定选型。
- [AscFloat2Int32](../scalar_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscInt322float》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscInt322Float](../reg/data_type_convert/asc_int322float.md)（`same_topic`）：AscInt322Float 与《AscInt322float》的实质衔接是：AscInt322Float 的 Vector 对应入口执行同一 int32→float 转换，AscFloat2Int32 则提供反向路径，用于核对舍入和 mask 置零契约。
<!-- cannbot:related:end -->
