---
type: API
title: 数据过滤
description: 提供Ascend C SIMD高阶API中的数据过滤接口，包含Select、DropOut及其Tiling临时空间大小查询接口。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_filter/data_filter.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 数据过滤

提供 Ascend C SIMD 高阶 API 中的数据过滤接口，包含 Select 条件筛选和 DropOut 随机丢弃两类算子。
每类算子均提供对应的 Tiling 临时空间大小查询接口（GetSelectMaxMinTmpSize、GetDropOutMaxMinTmpSize），用于在 Host 侧规划 Tiling 参数。
