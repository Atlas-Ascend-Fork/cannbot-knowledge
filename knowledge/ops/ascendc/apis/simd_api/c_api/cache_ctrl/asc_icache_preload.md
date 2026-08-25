---
type: API
title: AscIcachePreload
description: 从指令所在GM地址预加载指令到ICache中，支持配置预取长度。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_icache_preload.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscIcachePreload

从指令所在GM地址预加载数据到对应的cacheline中。

开发者手动调用该接口，能够从指令所在GM地址预加载指令到ICache中。

参数：addr(输入): 预加载数据的地址。；prefetch_len(输入): 预加载数据的长度，单位为2K Byte，取值需满足 。其中，AIC和AIV的ICache大小分别为32KB和16KB。

约束：prefetch_len参数单位为2K Byte，取值需满足 。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [删 smalle slim TU 致 e≤32 decode icache 税](../../../../runbooks/performance/smalle_slim_tu_e_32_decode_icache.md)（`exemplifies`）：AscIcachePreload 与《删 smalle slim TU 致 e≤32 decode icache 税》的实质衔接是：Icache preload 的 C/C++ 入口和状态查询成对使用；slim TU 实测卡验证 I-cache 取指压力的性能后果。
- [GetICachePreloadStatus](../../basic_api/cache_control/get_i_cache_preload_status_isasi.md)（`related`）：AscIcachePreload 与《GetICachePreloadStatus》的实质衔接是：Icache preload 的 C/C++ 入口和状态查询成对使用；slim TU 实测卡验证 I-cache 取指压力的性能后果。
- [AscGetIcachePreloadStatus](asc_get_icache_preload_status.md)（`same_topic`）：AscIcachePreload 与《AscGetIcachePreloadStatus》的实质衔接是：Icache preload 的 C/C++ 入口和状态查询成对使用；slim TU 实测卡验证 I-cache 取指压力的性能后果。
- [ICachePreLoad](../../basic_api/cache_control/i_cache_pre_load_isasi.md)（`same_topic`）：C API asc_icache_preload 与 C++ ICachePreLoad 提供相同指令缓存预取能力。
- [系统缓存概述（缓存控制）](../../basic_api/cache_control/system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《AscIcachePreload》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
