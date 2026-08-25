---
type: API
title: GetICachePreloadStatus
description: 调试接口，在ICachePreLoad后调用获取ICache预加载状态，返回0表示完成，返回1表示未完成。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/GetICachePreloadStatus_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetICachePreloadStatus

获取Instruction Cache预加载状态，查询当前指令Cache的预加载配置是否生效。

函数原型：bool GetICachePreloadStatus()。返回true表示预加载已开启，false表示未开启。用于查询指令Cache预加载状态。

<!-- cannbot:related:start -->
## 相关

- [AscIcachePreload](../../c_api/cache_ctrl/asc_icache_preload.md)（`related`）：AscIcachePreload 与《GetICachePreloadStatus》的实质衔接是：Icache preload 的 C/C++ 入口和状态查询成对使用；slim TU 实测卡验证 I-cache 取指压力的性能后果。
- [AscGetIcachePreloadStatus](../../c_api/cache_ctrl/asc_get_icache_preload_status.md)（`same_topic`）：GetICachePreloadStatus 是 C++ Basic API 的对应状态查询，返回值 0/1 与 AscGetIcachePreloadStatus 一致。
- [ICachePreLoad](i_cache_pre_load_isasi.md)（`same_topic`）：发起 ICachePreLoad 后用 GetICachePreloadStatus 查询完成状态，二者构成异步预加载闭环。
- [系统缓存概述（缓存控制）](system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《GetICachePreloadStatus》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
