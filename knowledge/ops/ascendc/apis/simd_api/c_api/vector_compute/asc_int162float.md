---
type: API
title: AscInt162float
description: 将int16_t类型数据转换为float类型。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int162float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt162float

将int16_t类型数据转换为float类型。
函数原型：void asc_int162float(__ubuf__ float* dst, __ubuf__ int16_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt162Float](../reg/data_type_convert/asc_int162float.md)（`related`）：两卡都定义 int16→float 转换；Reg 版本还要求按奇偶半区处理 1:2 位宽展开，UB 版本提供 count 型连续转换，可据布局选择路径。
<!-- cannbot:related:end -->
