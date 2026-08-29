---
type: API
title: asc_scatter
description: 该接口已废弃。请使用asc_scatter实现此功能。 该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程如下图所示：
  !scatter功能说明
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_scatter_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_scatter

该接口已废弃。请使用asc_scatter实现此功能。 该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程
函数原型：void asc_scatter(vector_int8_t& src, __ubuf__ int8_t* dst, vector_uint16_t index, vector_bool mask)
约束：dst首地址必须32B对齐。；当dst为int8_t或者uint8_t数据类型时，源操作数中仅偶数位元素有效。即src中的偶数位置[0, 2, 4, ..., 252, 254]的数据会被分散存储到目的操作数中。；index中的值必须唯一。若存在重复的index值，系统仅保留其中一个对应的数据，其余将被忽略。无法确定具体保留哪一个，因此必须确保index值不重复。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscScatter](asc_scatter.md)（`same_topic`）：该接口已废弃。请使用asc_scatter实现此功能。 该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程；该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程。废弃卡明确要求改用 asc_scatter，并描述相同的按 index 将 src 分散到 dst 的行为；目标卡就是当前替代接口及其功能合同。
<!-- cannbot:related:end -->
