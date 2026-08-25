---
type: API
title: AscInt322int16
description: 将int32_t类型数据转换为int16_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int322int16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt322int16

将int32_t类型数据转换为int16_t类型。
函数原型：void asc_int322int16(__ubuf__ int16_t* dst, __ubuf__ int32_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt162Int32](../reg/data_type_convert/asc_int162int32.md)（`related`）：该接口提供相反的 int16→int32 扩宽并按奇偶输入半段读取；与 focal 的 2:1 窄化一起说明往返转换的 lane 数和数据布局变化。
- [AscInt322Int16](../reg/data_type_convert/asc_int322int16.md)（`same_topic`）：两个 AscInt322Int16 入口都把 int32_t 转为 int16_t；Reg 版本补充 mask、奇偶 lane 写入及饱和控制，Memory Vector 版本提供 UB count 形式。
- [AscInt322Uint16](../reg/data_type_convert/asc_int322uint16.md)（`same_topic`）：AscInt322Uint16 与《AscInt322int16》的实质衔接是：AscInt322Uint16 是 32→16 位窄化并带饱和/奇偶 lane 布局；uint32→uint16 与 int32→int16 对照可分离符号解释和位宽布局。
<!-- cannbot:related:end -->
