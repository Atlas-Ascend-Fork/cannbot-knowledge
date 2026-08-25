---
type: API
title: AscInt322int64
description: 将int32_t类型数据转换为int64_t类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int322int64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt322int64

将int32_t类型数据转换为int64_t类型。
函数原型：void asc_int322int64(__ubuf__ int64_t* dst, __ubuf__ int32_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [Reg int32→int64 Cast 源目 VL 错配留空索引](../../../../runbooks/precision/int32_to_int64_reg_cast_must_respect_destination_lane_width.md)（`exemplifies`）：《AscInt322int64》处理“将int32_t类型数据转换为int64_t类型。”。《Reg int32→int64 Cast 源目 VL 错配留空索引》明确“以 int32 的 64-lane 步长驱动 int64 的 32-lane Reg Cast 时，每块后半索引未写；先以 Scalar 逐元素转换建立正确基线。”，可直接用于核对Reg int32/int64 双向转换及按目的 lane 宽度驱动 Cast 的正确性约束。
- [AscInt322Int64](../reg/data_type_convert/asc_int322int64.md)（`related`）：AscInt322Int64 与《AscInt322int64》的实质衔接是：AscInt32ToInt64 的 Reg 与 C 向量入口执行同一有符号扩宽，反向 Int64ToInt32 明确窄化时的溢出边界。
- [AscInt642int32](../reg/data_type_convert/asc_int642int32.md)（`related`）：《AscInt642int32》说明将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。；《AscInt322int64》说明将int32_t类型数据转换为int64_t类型。。二者在int64到int32窄化的饱和/非饱和语义需与反向扩宽及同源转换对照验证上存在可执行的直接衔接。
- [AscInt642int32](asc_int642int32.md)（`same_topic`）：《AscInt322int64》处理“将int32_t类型数据转换为int64_t类型。”。《AscInt642int32》明确“将int64_t类型数据转换为int32_t类型。”，可直接用于核对Reg int32/int64 双向转换及按目的 lane 宽度驱动 Cast 的正确性约束。
<!-- cannbot:related:end -->
