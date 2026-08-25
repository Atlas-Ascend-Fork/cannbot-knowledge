---
type: API
title: 索引计算
description: 提供Ascend C SIMD高阶API中的索引计算接口，包含Arange及GetArangeMaxMinTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.indexing]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/index_compute/index_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 索引计算

提供 Arange 等差数列生成接口及 GetArangeMaxMinTmpSize 临时空间查询接口。Arange 根据起始值、差值和长度生成等差数列，内部通过 SetValue 和 Adds 逐步扩充至目标长度。

接口为模板函数，Ascend 950PR/950DT 支持 int16_t、half、int32_t、float、int64_t；Atlas A3 系列支持 int16_t、half、int32_t、float。要求 `diffValue >= 0`、`count > 0`，仅支持 ND 格式。

<!-- cannbot:related:start -->
## 相关

- [Reg矢量计算索引操作](../../basic_api/reg_vector_compute/index_operations/index_operations.md)（`same_topic`）：Reg矢量计算索引操作 与《索引计算》的实质衔接是：Reg 索引操作与 C Reg 索引计算是同一 Arange/索引生成能力的跨层概述；具体成员关系由 part_of 覆盖。
<!-- cannbot:related:end -->
