---
type: API
title: 访存函数
description: 提供加载、存储、缓存控制等访存接口。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/memory_access_functions/memory_access_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 访存函数

提供 AICore SIMT 编程模型下的显式访存控制接口，包括全局内存加载（asc_ldcg、asc_ldca）、存储（asc_stcg、asc_stwt）、缓存无效化（asc_dcci_single、asc_dcci_entire）和空操作占位（asc_nop）。通过不同的加载存储策略和缓存提示，支持精细化的访存性能调优。
