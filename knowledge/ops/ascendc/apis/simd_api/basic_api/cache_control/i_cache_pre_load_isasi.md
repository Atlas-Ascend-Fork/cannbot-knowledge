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

- [kernel 源码改动未生效因 binary 缓存](../../../../runbooks/compilation/kernel_binary_cache_printf_hash_toggle.md)（`exemplifies`）：该卡处理 kernel binary 缓存旧代码而非 ICache 指令预取；二者可按“重启后是否仍旧 binary”分流。
- [删 smalle slim TU 致 e≤32 decode icache 税](../../../../runbooks/performance/smalle_slim_tu_e_32_decode_icache.md)（`exemplifies`）：该性能卡用 TU 规模 A/B 和 profile 判断 ICache 压力，能验证预加载是否解决真实前端瓶颈。
- [AscGetIcachePreloadStatus](../../c_api/cache_ctrl/asc_get_icache_preload_status.md)（`related`）：ICachePreLoad 是 Basic API 侧对应的预加载发起接口，与状态查询组成另一套完整调用链。
- [AscIcachePreload](../../c_api/cache_ctrl/asc_icache_preload.md)（`same_topic`）：C API asc_icache_preload 与 C++ ICachePreLoad 提供相同指令缓存预取能力。
- [GetICachePreloadStatus](get_i_cache_preload_status_isasi.md)（`same_topic`）：发起 ICachePreLoad 后用 GetICachePreloadStatus 查询完成状态，二者构成异步预加载闭环。
- [系统缓存概述（缓存控制）](system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《ICachePreLoad》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
