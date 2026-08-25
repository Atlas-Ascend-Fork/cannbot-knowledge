---
type: API
title: 缓存控制
description: AscendC 矢量计算基础 API 的缓存控制接口集，包含 DataCachePreload、DataCacheCleanAndInvalid、ICachePreLoad 等。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/cache_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 缓存控制

Ascend C 矢量计算基础 API 缓存控制接口集，提供对系统数据缓存与指令缓存的预取与清理操作。
包含 DataCachePreload 数据缓存预取、DataCacheCleanAndInvalid 数据缓存清理与失效，以及 ISASI 专属的 ICachePreLoad/GetICachePreloadStatus 指令缓存预取与状态查询。
用于优化数据搬运效率与保证缓存一致性。
