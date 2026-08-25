---
type: API
title: DataCachePreload
description: 从GM地址预加载数据到DCache，每次调用预加载一个Cache Line大小的数据，提升后续访问效率。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/DataCachePreload.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DataCachePreload

预加载GM数据到Data Cache，提前将指定GM地址的数据加载到Cache中，后续Scalar单元读取时可直接命中Cache，减少访存延迟。

函数原型提供基于GM地址和长度的预加载方式。参数包含GM地址指针和数据长度。约束：与DataCacheCleanAndInvalid配合使用管理Cache一致性。头文件：basic_api/kernel_operator_cache_intf.h。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《DataCachePreload》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [DCacheAccess](../../../../guides/operator_practice/simt_operator_optimization/memory_access/dcache_access.md)（`explains`）：DataCachePreload 与《DCacheAccess》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [缓存一致性](../../../../guides/programming_guide/advanced_programming/memory_model/cache_coherence.md)（`explains`）：DataCachePreload 与《缓存一致性》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [AscDcci](../../c_api/cache_ctrl/asc_dcci.md)（`related`）：DataCachePreload 与《AscDcci》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [DataCacheCleanAndInvalid](data_cache_clean_and_invalid.md)（`related`）：DataCachePreload 与《DataCacheCleanAndInvalid》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [ReadGmByPassDCache](../scalar_compute/read_gm_by_pass_d_cache_isasi.md)（`related`）：DataCachePreload 与《ReadGmByPassDCache》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [asc_datacache_preload](../../c_api/cache_ctrl/asc_datacache_preload.md)（`same_topic`）：DataCachePreload 与《asc_datacache_preload》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [系统缓存概述（缓存控制）](system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《DataCachePreload》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
