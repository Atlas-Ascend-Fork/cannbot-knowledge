---
type: API
title: 排序操作
description: 排序操作接口导航页，涵盖TopK、Sort、MrgSort、Concat、Extract等排序与拼接接口。
tags: [task.lookup, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/sort_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 排序操作

Ascend C SIMD 高阶 API 排序与拼接导航页，提供 TopK、Sort、MrgSort 等排序算子及 Concat、Extract 等张量操作接口。
TopK 和 Sort 均提供对应的 Tiling 接口与临时空间查询方法（GetSortTmpSize、GetSortMaxMinTmpSize、GetSortOffset、GetSortLen、GetConcatTmpSize）。
MrgSort 用于多路归并排序场景，支持分段有序数据的合并。
