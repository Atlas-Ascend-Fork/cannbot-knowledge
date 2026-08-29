---
type: API
title: AscStoreL2CacheMode
description: 表示数据从UB搬运到GM时的L2 cache策略，在调用asc_copy_ub2gm_align时使用。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/enum/asc_store_l2_cache_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# AscStoreL2CacheMode

表示数据从UB搬运到GM时的L2 Cache策略，在调用asc_copy_ub2gm_align时使用。枚举值：NORMAL_FIRST_VICTIM（启用Cache，高替换优先级）、NORMAL_LAST_VICTIM（启用Cache，低替换优先级）、NORMAL_PERSISTENT（启用Cache，驻留模式）、NOTALLOC_CLEAN（不启用Cache，标记为Clean后丢弃）。相比asc_load_l2_cache_mode少了NOTALLOC_KEEP和NOTALLOC_DROP，因为Store场景下这些策略不适用。
