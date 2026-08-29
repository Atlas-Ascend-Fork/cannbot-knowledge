---
type: API
title: ICachePreLoad
description: 从指令所在GM地址预加载指令到ICache中，支持配置预取长度，提升指令读取效率。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/ICachePreLoad_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# ICachePreLoad

预加载指令到Instruction Cache，提前将指定地址的指令加载到ICache中，减少指令取指延迟，提升执行性能。

函数原型提供基于地址和长度的预加载方式。参数包含指令地址和长度。约束：与GetICachePreloadStatus配合使用。头文件：basic_api/kernel_operator_cache_intf.h。

<!-- cannbot:related:start -->
## 相关

- [GetICachePreloadStatus](get_i_cache_preload_status_isasi.md)（`related`）：“获取Instruction Cache预加载状态，查询当前指令Cache的预加载配置是否生效。”与“约束：与GetICachePreloadStatus配合使用。头文件：basic_api/kernel_operator_cache_intf.h。”分别给出两端正文事实；ICachePreLoad 发起指令预加载，GetICachePreloadStatus 查询该配置是否生效，构成同一预加载操作的提交与状态确认链。
<!-- cannbot:related:end -->
