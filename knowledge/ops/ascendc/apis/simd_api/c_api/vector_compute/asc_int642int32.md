---
type: API
title: AscInt642int32
description: 将int64_t类型数据转换为int32_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int642int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt642int32

将int64_t类型数据转换为int32_t类型。
函数原型：void asc_int642int32(__ubuf__ int32_t* dst, __ubuf__ int64_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt642Float](../reg/data_type_convert/asc_int642float.md)（`related`）：AscInt642Float 与《AscInt642int32》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [AscInt322int64](asc_int322int64.md)（`same_topic`）：《AscInt322int64》处理“将int32_t类型数据转换为int64_t类型。”。《AscInt642int32》明确“将int64_t类型数据转换为int32_t类型。”，可直接用于核对Reg int32/int64 双向转换及按目的 lane 宽度驱动 Cast 的正确性约束。
- [AscInt642int32](../reg/data_type_convert/asc_int642int32.md)（`same_topic`）：两个 AscInt642Int32 入口都把 int64_t 转为 int32_t；Reg 版本用 mask 和饱和控制，Memory Vector 版本用 UB count 调用。
<!-- cannbot:related:end -->
