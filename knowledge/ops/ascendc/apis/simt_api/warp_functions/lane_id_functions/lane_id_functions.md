---
type: API
title: Lane ID类函数
description: 提供Lane ID获取与Lane掩码比较接口。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/lane_id_functions/lane_id_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Lane ID类函数

提供 Warp 内 Lane 标识的查询接口，包括当前 Lane 编号获取（laneid）和基于 Lane 编号的掩码比较（lanemask_eq、lanemask_le、lanemask_lt、lanemask_ge、lanemask_gt）。掩码函数返回活跃 Lane 集合的位掩码，用于 Warp 级别的条件控制与数据同步。
