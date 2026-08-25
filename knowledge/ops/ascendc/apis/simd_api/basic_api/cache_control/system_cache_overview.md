---
type: API
title: 系统缓存概述（缓存控制）
description: Cache（缓存）的主要作用是在搬运单元或Scalar单元与外部存储之间提供一层高速缓冲，以降低数据访问延迟并提高带宽利用率。通常情况下，被频繁访问的数据会写入Cache，搬运单元或Scalar单元在执行过程中优先从Cache中读取数据；当Cache未命中时，再从外部存储加载数据并更新到Cache中。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/system_cache_overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Cache系统总览

Ascend AI Core内部包含多种Cache：Data Cache（用于Scalar单元访问GM时的数据缓存）和Instruction Cache（用于指令预取）。DMA搬运单元直接访问GM不经过Cache，因此DMA与Scalar之间存在Cache一致性问题。

Cache一致性管理：DMA写入GM后Scalar读取前需调用DataCacheCleanAndInvalid清除旧Cache；Scalar频繁读取同一GM数据可使用DataCachePreload预加载提升性能；指令执行密集场景可使用ICachePreLoad预取指令。Cache控制接口仅影响Scalar单元的访存行为，不影响DMA搬运。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《系统缓存概述（缓存控制）》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [AscDcci](../../c_api/cache_ctrl/asc_dcci.md)（`related`）：AscDcci 与《系统缓存概述（缓存控制）》的实质衔接是：AscDcci 的 single/entire 变体与 C++ DataCacheCleanAndInvalid 操作同一 DCache；缓存概述、L2 驱逐故障和编译选项提供验证与尾开销决策。
- [缓存控制](../../c_api/cache_ctrl/cache_control.md)（`related`）：缓存控制 与《系统缓存概述（缓存控制）》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [AscIcachePreload](../../c_api/cache_ctrl/asc_icache_preload.md)（`same_topic`）：系统缓存概述（缓存控制） 与《AscIcachePreload》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [DataCacheCleanAndInvalid](data_cache_clean_and_invalid.md)（`same_topic`）：系统缓存概述（缓存控制） 与《DataCacheCleanAndInvalid》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [DataCachePreload](data_cache_preload.md)（`same_topic`）：系统缓存概述（缓存控制） 与《DataCachePreload》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [GetICachePreloadStatus](get_i_cache_preload_status_isasi.md)（`same_topic`）：系统缓存概述（缓存控制） 与《GetICachePreloadStatus》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [ICachePreLoad](i_cache_pre_load_isasi.md)（`same_topic`）：系统缓存概述（缓存控制） 与《ICachePreLoad》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [SetL2CacheHint](../data_structures/global_tensor/set_l2_cache_hint.md)（`same_topic`）：系统缓存概述（缓存控制） 与《SetL2CacheHint》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
- [asc_datacache_preload](../../c_api/cache_ctrl/asc_datacache_preload.md)（`same_topic`）：系统缓存概述（缓存控制） 与《asc_datacache_preload》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
