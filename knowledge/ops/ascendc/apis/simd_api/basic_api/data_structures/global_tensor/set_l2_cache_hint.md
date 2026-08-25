---
type: API
title: SetL2CacheHint
description: 设置GlobalTensor是否启用L2 Cache，默认启用L2 Cache。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetL2CacheHint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetL2CacheHint

设置 GlobalTensor 是否启用 L2 Cache，默认启用。函数签名为 template<CacheRwMode rwMode = CacheRwMode::RW> void SetL2CacheHint(CacheMode mode)。
参数 mode 指定 L2 Cache 模式：CACHE_MODE_DISABLE 禁用、CACHE_MODE_NORMAL 普通模式（默认，容量满时触发置换）、CACHE_MODE_PERSISTENT 驻留模式（开发中，暂不支持）。
模板参数 rwMode 为读写模式预留参数（READ/WRITE/RW），使用默认值即可。
当特定 GlobalTensor 启用 L2 Cache 后性能反而下降时可手动禁用，例如仅对单次读取的 Tensor 关闭缓存以避免额外搬运开销。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《SetL2CacheHint》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [L2CacheSplit](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_split.md)（`explains`）：L2CacheSplit 与《SetL2CacheHint》的衔接是：大数据 L2CacheSplit 的分块策略由 Matmul L2 split 案例落地，L2 hint 与 load/store cache mode 决定分块数据是否按预期进入和复用 L2。
- [设置合理的L2 CacheMode](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：The guide explains why one-shot tensors may disable L2 while reused tensors should remain cached, and shows SetL2CacheHint as the control point.
- [高阶性能打磨](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/add_vector_operator/advanced_optimization.md)（`explains`）：该优化用 SetL2CacheHint(CACHE_MODE_DISABLE) 绕过只读一次输入的 L2，给出 28.9% 搬运耗时下降的具体选型证据。
- [SetValue](set_value.md)（`related`）：《SetValue》的任务是“设置GlobalTensor指定偏移位置的元素值，操作先写入DCache，需配合DataCacheCleanAndInvalid确保一致性。”。《SetL2CacheHint》具体提供“设置GlobalTensor是否启用L2 Cache，默认启用L2 Cache。”，它直接用于GlobalTensor 标量写入后的 DCache 可见性与 GetValue 验证。
- [系统缓存概述（缓存控制）](../../cache_control/system_cache_overview.md)（`same_topic`）：系统缓存概述（缓存控制） 与《SetL2CacheHint》的实质衔接是：系统缓存由 DCache/ICache 预取、DCache 清理失效、L2 hint 与 DCCI 共同控制；一致性错误卡给出清理接口必须指定目标 tensor 的调用约束。
<!-- cannbot:related:end -->
