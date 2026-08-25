---
type: API
title: AscInt642float
description: 将int64_t类型数据转换为float类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int642float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt642float

将int64_t类型数据转换为float类型。
函数原型：void asc_int642float_rd(__ubuf__ float* dst, __ubuf__ int64_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt642Float](../reg/data_type_convert/asc_int642float.md)（`related`）：AscInt642Float 与《AscInt642float》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [__ll2float_rd](../../../simt_api/math_functions/data_type_conversion/type_conversion_functions/_ll2float_rd.md)（`related`）：__ll2float_rd 是同一 FLOOR int64→float 的 SIMT 标量形式，提供 2^24/2^53 邻近整数的舍入例子，可作为线程标量实现和数值验证对照。
<!-- cannbot:related:end -->
