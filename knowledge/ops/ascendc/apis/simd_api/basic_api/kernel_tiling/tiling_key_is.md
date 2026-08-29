---
type: API
title: TILING_KEY_IS
description: 在核函数中判断本次执行时的tiling_key是否等于host侧运行时设置的某个key，从而标识tiling_key==key的一条kernel分支。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/TILING_KEY_IS.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TILING_KEY_IS

在核函数中判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key，标识 tiling_key==key 的 kernel 分支。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [IcpuSetTilingKey](../debug_interface/cpu_twin_debug/icpu_set_tiling_key.md)（`related`）：指定本次CPU调测使用的tilingKey；判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key；连接调测 key 设置与 Kernel 分支消费。
- [REGISTER_TILING_FOR_TILINGKEY](register_tiling_for_tilingkey.md)（`same_topic`）：判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key；注册与 TilingKey 相匹配的 TilingData 结构体。REGISTER_TILING_FOR_TILINGKEY 先把 key 条件映射到 TilingData，TILING_KEY_IS 再在 kernel 中选择相同 key 的执行分支；两者共同保证数据结构和代码分支匹配。
<!-- cannbot:related:end -->
