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

- [asc_datacache_preload](../../c_api/cache_ctrl/asc_datacache_preload.md)（`same_topic`）：从源地址所在的特定GM地址预加载数据到Data Cache中，每次调用只能预加载一个Cache Line大小的数据。；预加载GM数据到Data Cache，提前将指定GM地址的数据加载到Cache中，后续Scalar单元读取时可直接命中Cache，减少访存延迟。。两卡描述同一 GM→Data Cache 预加载能力的 C API 与基础 API 表达，均服务后续 Scalar 访问命中。
<!-- cannbot:related:end -->
