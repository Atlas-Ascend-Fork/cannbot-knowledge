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

- [AscNdimCopyGm2ub](../vector_data_move/asc_ndim_copy_gm2ub.md)（`related`）：“表示数据从GM搬运到UB时的L2 Cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。”与“函数原型：void asc_ndim_copy_gm2ub(__ubuf__ int8_t* dst, __gm__ int8_t* src, uint32_t loop0_size, uint32_t loop1_size, uint32_t loop2_size, uint32_t loop3_size, uint32_t loop4_size, uint8_t loop0_lp_count, uint8_t loop0_rp_count, bool padding_mode, asc_load_l2_cache_mode l2_cache_mode)”分别给出双端正文事实；枚举卡定义 GM 到 UB 搬运的 L2 管理策略，asc_ndim_copy_gm2ub 将该枚举作为直接 l2_cache_mode 参数，连接缓存策略选择与多维搬运调用。
<!-- cannbot:related:end -->
