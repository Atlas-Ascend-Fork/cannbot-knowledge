---
type: API
title: AscGetIcachePreloadStatus
description: 调试接口，在asc_icache_preload后调用获取ICache预加载状态，返回0表示完成，1表示未完成。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_get_icache_preload_status.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# AscGetIcachePreloadStatus

获取ICache的Preload的状态。

该接口为调试接口，在asc_icache_preload后调用，用于获取ICache的PreLoad的状态。当返回值为0时，说明ICache的PreLoad已完成；当返回值为1时，说明ICache的PreLoad未完成。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [ICachePreLoad](../../basic_api/cache_control/i_cache_pre_load_isasi.md)（`related`）：ICachePreLoad 是 Basic API 侧对应的预加载发起接口，与状态查询组成另一套完整调用链。
- [AscIcachePreload](asc_icache_preload.md)（`same_topic`）：AscIcachePreload 与《AscGetIcachePreloadStatus》的实质衔接是：Icache preload 的 C/C++ 入口和状态查询成对使用；slim TU 实测卡验证 I-cache 取指压力的性能后果。
- [GetICachePreloadStatus](../../basic_api/cache_control/get_i_cache_preload_status_isasi.md)（`same_topic`）：GetICachePreloadStatus 是 C++ Basic API 的对应状态查询，返回值 0/1 与 AscGetIcachePreloadStatus 一致。
<!-- cannbot:related:end -->
