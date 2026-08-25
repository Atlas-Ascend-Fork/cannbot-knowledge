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

<!-- cannbot:related:start -->
## 相关

- [TopK BF16 tie 索引顺序与 CPU 不一致](../../../../runbooks/precision/topk_bf16_tie_cpu.md)（`exemplifies`）：TopK BF16 tie 索引顺序与 CPU 不一致 与《排序操作》的实质衔接是：TopK 对 tie 不保证与 CPU 相同的索引顺序；TopK/tiling 与 Sort→MrgSort→Concat/Extract 链解释内部排序，fair-oracle 卡给出集合而非逐元素索引的验证方式。
<!-- cannbot:related:end -->
