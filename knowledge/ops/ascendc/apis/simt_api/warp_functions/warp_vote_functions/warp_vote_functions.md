---
type: API
title: Warp Vote类函数
description: 提供Warp级别的投票与掩码接口。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_vote_functions/Warp_vote_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp Vote类函数

提供 Warp 内的投票表决接口，包括全量判定（asc_all）、任一判定（asc_any）、位掩码收集（asc_ballot）和活跃掩码获取（asc_activemask）。这些函数对 Warp 内所有活跃 Lane 的布尔条件进行聚合，返回 Warp 级别的判定结果或位掩码，用于条件分支优化。
