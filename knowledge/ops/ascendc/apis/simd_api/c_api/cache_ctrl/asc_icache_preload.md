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

- [AscGetIcachePreloadStatus](asc_get_icache_preload_status.md)（`related`）：开发者手动调用该接口，能够从指令所在GM地址预加载指令到ICache中。；该接口为调试接口，在asc_icache_preload后调用，用于获取ICache的PreLoad的状态。前者发起预加载，后者在同一调用链中判定完成状态。
<!-- cannbot:related:end -->
