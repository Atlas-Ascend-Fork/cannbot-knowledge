---
type: API
title: AscLoadL2CacheMode
description: 表示数据从GM搬运到UB时的L2 cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/enum/asc_load_l2_cache_mode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# AscLoadL2CacheMode

表示数据从GM搬运到UB时的L2 Cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。枚举值：NORMAL_FIRST_VICTIM（启用Cache，高替换优先级）、NORMAL_LAST_VICTIM（启用Cache，低替换优先级）、NORMAL_PERSISTENT（启用Cache，驻留模式）、NOTALLOC_KEEP（不启用Cache，保持已有Cache Line）、NOTALLOC_CLEAN（不启用Cache，标记为Clean后丢弃）、NOTALLOC_DROP（不启用Cache，直接丢弃）。合理配置可提升数据搬运效率。

<!-- cannbot:related:start -->
## 相关

- [L2CacheSplit](../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md)（`explains`）：L2CacheSplit 与《AscLoadL2CacheMode》的衔接是：大数据 L2CacheSplit 的分块策略由 Matmul L2 split 案例落地，L2 hint 与 load/store cache mode 决定分块数据是否按预期进入和复用 L2。
- [设置合理的L2 CacheMode](../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：AscLoadL2CacheMode说明表示数据从GM搬运到UB时的L2 cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。
- [AscCopyGm2UbAlign](../vector_data_move/asc_copy_gm2ub_align/asc_copy_gm2ub_align.md)（`related`）：AscCopyGm2UbAlign 直接接收 asc_load_l2_cache_mode，用它选择启用、驻留或 bypass L2 的 GM→UB 搬运策略。
- [AscNdimCopyGm2ub](../vector_data_move/asc_ndim_copy_gm2ub.md)（`related`）：AscNdimCopyGm2ub 的最后一个参数就是 asc_load_l2_cache_mode，多维搬入时同样用该枚举控制 L2 分配策略。
- [AscStoreL2CacheMode](asc_store_l2_cache_mode.md)（`related`）：Store 模式控制 UB→GM 写侧 L2 行为，Load 模式控制 GM→UB 读侧行为；两者枚举含义不可混用，需按搬运方向选型。
- [asc_ldcg（内存访问函数）](../../../simt_api/memory_access_functions/asc_ldcg.md)（`same_topic`）：asc_ldcg（内存访问函数） 与《AscLoadL2CacheMode》的实质衔接是：asc_ldcg 通过 L2 cache 读取 GM，stcg 是写回配对，DCCI 用于失效缓存；L2 模式和 Scalar 访存指南共同决定命中策略与一致性。
<!-- cannbot:related:end -->
