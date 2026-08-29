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

- [AscIcachePreload](asc_icache_preload.md)（`related`）：开发者手动调用该接口，能够从指令所在GM地址预加载指令到ICache中。；该接口为调试接口，在asc_icache_preload后调用，用于获取ICache的PreLoad的状态。前者发起预加载，后者在同一调用链中判定完成状态。
<!-- cannbot:related:end -->
