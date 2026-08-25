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

<!-- cannbot:related:start -->
## 相关

- [L2CacheSplit](../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md)（`explains`）：L2CacheSplit 与《AscStoreL2CacheMode》的衔接是：大数据 L2CacheSplit 的分块策略由 Matmul L2 split 案例落地，L2 hint 与 load/store cache mode 决定分块数据是否按预期进入和复用 L2。
- [设置合理的L2 CacheMode](../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：AscStoreL2CacheMode说明表示数据从UB搬运到GM时的L2 cache策略，在调用asc_copy_ub2gm_align时使用。
- [AscCopyUb2GmAlign](../vector_data_move/asc_copy_ub2gm_align/asc_copy_ub2gm_align.md)（`related`）：AscCopyUb2GmAlign 直接接收 asc_store_l2_cache_mode 来控制写回后的 L2 分配/淘汰，是该枚举的具体消费者。
- [AscLoadL2CacheMode](asc_load_l2_cache_mode.md)（`related`）：Store 模式控制 UB→GM 写侧 L2 行为，Load 模式控制 GM→UB 读侧行为；两者枚举含义不可混用，需按搬运方向选型。
- [AscStoreDev](../scalar_compute/asc_store_dev.md)（`related`）：StoreDev 的 L2 cache mode 决定写是否进入 L2。
- [asc_stwt（内存访问函数）](../../../simt_api/memory_access_functions/asc_stwt.md)（`same_topic`）：asc_stwt（内存访问函数） 与《AscStoreL2CacheMode》的实质衔接是：asc_stwt 把数据写入 GM 并缓存到 DCache/L2；stcg/ldcg、缓存模式和 DCCI 共同决定写策略、后续读取及显式失效时机。
<!-- cannbot:related:end -->
