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
