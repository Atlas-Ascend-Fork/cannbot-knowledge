---
type: API
title: Warp函数
description: Warp函数索引，包含Vote、Shfl、Reduce与Lane ID类函数。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# Warp函数

Warp 级别协同操作函数的总入口，包含 Warp Vote（投票表决）、Warp Shfl（数据交换）、Warp Reduce（归约）和 Lane ID（通道标识）四类函数。这些函数以 Warp（通常 32 个 Lane）为最小协同单位，支持 Warp 内的并行数据交换、条件聚合和归约运算。
