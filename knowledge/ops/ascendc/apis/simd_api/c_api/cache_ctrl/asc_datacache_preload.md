---
type: API
title: asc_datacache_preload
description: 从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
tags: [task.lookup, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_datacache_preload.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---
# asc_datacache_preload

从源地址所在的特定GM地址预加载数据到Data Cache中，每次调用只能预加载一个Cache Line大小的数据。

参数：address(输入): 源操作数的起始地址。；offset(输入): 在源操作数上偏移offset大小开始加载数据，单位为Bytes。

约束：频繁调用此接口可能会导致保留栈拥塞，此时，该接口将被视为NOP指令，阻塞Scalar流水。因此不建议频繁调用此接口。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《asc_datacache_preload》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [DataCachePreload](../../basic_api/cache_control/data_cache_preload.md)（`same_topic`）：DataCachePreload 与《asc_datacache_preload》的实质衔接是：DataCachePreload 是 GM 数据进入 DCache 的预取动作；清理失效、旁路读、DCCI 与一致性指南共同定义预取后可见性、失效和访问优化的完整契约。
- [系统缓存概述（缓存控制）](../../basic_api/cache_control/system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《asc_datacache_preload》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
