---
type: API
title: 索引操作
description: 寄存器侧索引操作类接口汇总，提供arange等序列生成能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/index_operate/index_operate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 索引操作

提供 asc_arange 接口，以传入 value 为起始值生成递增或递减索引序列，保存在 dst 中。递增模式生成 {value, value+1, ..., value+VL_T-1}，递减模式生成 {value+VL_T-1, ..., value+1, value}，其中 VL_T 为矢量数据寄存器可存储的元素数量。

支持 int8_t、int16_t、half、int32_t、float 数据类型。该接口仅在 AIV 上生效。仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算索引操作](../../../basic_api/reg_vector_compute/index_operations/index_operations.md)（`same_topic`）：Reg矢量计算索引操作 与《索引操作》的实质衔接是：Reg 索引操作与 C Reg 索引计算是同一 Arange/索引生成能力的跨层概述；具体成员关系由 part_of 覆盖。
<!-- cannbot:related:end -->
