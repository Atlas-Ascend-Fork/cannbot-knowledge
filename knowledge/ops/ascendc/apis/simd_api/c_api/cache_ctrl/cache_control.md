---
type: API
title: 缓存控制
description: 缓存控制接口索引页，包含asc_datacache_preload、asc_dcci、asc_dci及asc_icache_preload等。
tags: [task.lookup, topic.implementation.api_layer.c_api, topic.data_movement.memory_access]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/cache_control.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 缓存控制

提供数据缓存与指令缓存的预取及无效化控制接口。asc_datacache_preload预取数据缓存，asc_dcci/asc_dci无效化数据缓存行，asc_icache_preload预取指令缓存，asc_get_icache_preload_status查询预取状态。
适用于需要优化内存访问延迟或保证缓存一致性的场景，通过控制缓存行为提升数据搬运和计算指令的执行效率。

<!-- cannbot:related:start -->
## 相关

- [DataCacheCleanAndInvalid 无参调用导致编译失败](../../../../runbooks/compilation/datacache_clean_requires_tensor_target.md)（`exemplifies`）：DataCacheCleanAndInvalid 无参调用导致编译失败 与《缓存控制》的实质衔接是：编译失败源于把 DataCacheCleanAndInvalid 臆造成无参全缓存调用；真实 Tensor 目标 API、preload/cache 总览、L2 hint 和 DCI 写回故障说明缓存操作必须绑定对象与执行边界。
- [DCacheAccess](../../../../guides/operator_practice/simt_operator_optimization/memory_access/dcache_access.md)（`explains`）：缓存控制 与《DCacheAccess》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [缓存一致性](../../../../guides/programming_guide/advanced_programming/memory_model/cache_coherence.md)（`explains`）：C API 缓存控制为 C 扩展层提供同类维护原语，需按实际编程模型选择。
- [设置DCI编译选项来减少算子尾开销](../../../../guides/operator_practice/simd_operator_optimization/overhead_optimization/dci_compile_option.md)（`explains`）：缓存控制 与《设置DCI编译选项来减少算子尾开销》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [系统缓存概述（缓存控制）](../../basic_api/cache_control/system_cache_overview.md)（`related`）：缓存控制 与《系统缓存概述（缓存控制）》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [缓存控制](../../basic_api/cache_control/cache_control.md)（`related`）：缓存控制 与《缓存控制》的实质衔接是：C 缓存控制页覆盖 DCache/ICache 预取与失效；系统缓存、缓存一致性、DCI 优化和无参清理编译失败补充作用域、目标对象及使用边界。
- [asc_dcci_entire](../../../simt_api/memory_access_functions/asc_dcci_entire.md)（`same_topic`）：asc_dcci_entire 与《缓存控制》的实质衔接是：asc_dcci_entire 刷新整个 DCache，而 single 只针对地址；ldcg/stcg、C DCCI、缓存控制和 DCache 指南共同定义何时绕过或失效缓存。
<!-- cannbot:related:end -->
