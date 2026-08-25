---
type: API
title: 排序组合（ISASI）
description: ISASI排序组合接口索引页，汇总ProposalConcat、ProposalExtract、RpSort16、MrgSort4、Sort32等。
tags: [task.lookup, topic.compute.ordering]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/sort_and_merge_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# 排序组合（ISASI）

ISASI 场景下的矢量排序与组合接口集合。RpSort16/Sort32/MrgSort4/MrgSort 提供排序与归并能力；ProposalConcat/ProposalExtract 用于 proposal 数据的拼接与提取；GetMrgSortResult 查询归并结果。主要用于检测等需要排序选择的场景，属 ISASI 专属接口。
