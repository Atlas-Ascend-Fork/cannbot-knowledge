---
type: API
title: 系统缓存概述（缓存控制）
description: Cache（缓存）的主要作用是在搬运单元或Scalar单元与外部存储之间提供一层高速缓冲，以降低数据访问延迟并提高带宽利用率。通常情况下，被频繁访问的数据会写入Cache，搬运单元或Scalar单元在执行过程中优先从Cache中读取数据；当Cache未命中时，再从外部存储加载数据并更新到Cache中。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/system_cache_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Cache系统总览

Ascend AI Core内部包含多种Cache：Data Cache（用于Scalar单元访问GM时的数据缓存）和Instruction Cache（用于指令预取）。DMA搬运单元直接访问GM不经过Cache，因此DMA与Scalar之间存在Cache一致性问题。

Cache一致性管理：DMA写入GM后Scalar读取前需调用DataCacheCleanAndInvalid清除旧Cache；Scalar频繁读取同一GM数据可使用DataCachePreload预加载提升性能；指令执行密集场景可使用ICachePreLoad预取指令。Cache控制接口仅影响Scalar单元的访存行为，不影响DMA搬运。
