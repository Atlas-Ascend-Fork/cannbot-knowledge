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

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《缓存控制》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [缓存一致性](../../../../guides/programming_guide/advanced_programming/memory_model/cache_coherence.md)（`explains`）：缓存控制卡说明何时预取、清理 DCache/ICache，指南补充 Cache Line 粒度以及 DCache、ICache、SIMT DCache 与 GM 的一致性机制，帮助判断应使用哪类控制操作。
- [缓存控制](../../c_api/cache_ctrl/cache_control.md)（`related`）：缓存控制 与《缓存控制》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [DataCacheCleanAndInvalid](data_cache_clean_and_invalid.md)（`same_topic`）：缓存控制总页说明 clean、invalid、preload 的作用范围和组合，是本接口的机制入口。
<!-- cannbot:related:end -->
