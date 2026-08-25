---
type: API
title: AscFloat2Int32
description: 将float类型转换为int32_t类型，支持RINT、ROUND、FLOOR、CEIL四种舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_float2int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# AscFloat2Int32

将float类型转化为int32_t类型，并支持多种舍入模式。 舍入模式：
函数原型：int32_t asc_float2int32_rn(float value)
返回值：目的操作数（标量），value精度转换成int32_t的结果。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Ceil](../../adv_api/math_compute/ceil_interface/ceil.md)（`related`）：AscFloat2Int32 与《Ceil》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [Floor](../../adv_api/math_compute/floor_interface/floor.md)（`related`）：AscFloat2Int32 与《Floor》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [Rint](../../adv_api/math_compute/rint_interface/rint.md)（`related`）：AscFloat2Int32 与《Rint》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [Round](../../adv_api/math_compute/round_interface/round.md)（`related`）：AscFloat2Int32 与《Round》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscBfloat162int32](../vector_compute/asc_bfloat162int32.md)（`same_topic`）：AscFloat2Int32 与《AscBfloat162int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscFloat2Int32](../reg/data_type_convert/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2Int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscFloat2int16](../vector_compute/asc_float2int16.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2int16》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscFloat2int32](../vector_compute/asc_float2int32.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscFloat2int64](../vector_compute/asc_float2int64.md)（`same_topic`）：AscFloat2Int32 与《AscFloat2int64》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscHalf2int32](../vector_compute/asc_half2int32.md)（`same_topic`）：AscFloat2Int32 与《AscHalf2int32》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [AscInt322float](../vector_compute/asc_int322float.md)（`same_topic`）：AscFloat2Int32 与《AscInt322float》的实质衔接是：AscFloat2Int32 的四种舍入模式对应 Rint/Round/Floor/Ceil，相关 float/half/bfloat16 转换卡用于保持目标位宽、源类型和逆转换契约。
- [CastFloatToHalfInt32](../../basic_api/scalar_compute/cast_float_to_half_int32.md)（`same_topic`）：《CastFloatToHalfInt32》说明将float类型标量数据转换为half或int32_t类型标量数据，支持多种舍入模式。；《AscFloat2Int32》说明将float类型转换为int32_t类型，支持RINT、ROUND、FLOOR、CEIL四种舍入模式。。二者在标量float窄化依赖目标类型和RoundMode；同方向转换及命名空间故障卡直接说明其调用边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
