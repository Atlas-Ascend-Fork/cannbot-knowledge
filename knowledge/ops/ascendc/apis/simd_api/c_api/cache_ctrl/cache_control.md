---
type: API
title: 缓存控制
description: 缓存控制接口索引页，包含asc_datacache_preload、asc_dcci、asc_dci及asc_icache_preload等。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/cache_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 缓存控制

提供数据缓存与指令缓存的预取及无效化控制接口。asc_datacache_preload预取数据缓存，asc_dcci/asc_dci无效化数据缓存行，asc_icache_preload预取指令缓存，asc_get_icache_preload_status查询预取状态。
适用于需要优化内存访问延迟或保证缓存一致性的场景，通过控制缓存行为提升数据搬运和计算指令的执行效率。
