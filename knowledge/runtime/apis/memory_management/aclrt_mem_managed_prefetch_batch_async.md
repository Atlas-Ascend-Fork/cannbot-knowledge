---
type: API
title: aclrtMemManagedPrefetchBatchAsync
description: "在指定 Stream 上批量预取 UVM，用索引数组将各内存段分组映射到目标物理位置；地址与长度数组须等长。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.data_movement
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-05_unified_addressing.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- a3
- a2
---
# aclrtMemManagedPrefetchBatchAsync

## 功能说明

批量异步预取 UVM 内存到指定位置。

## 函数原型

```c
aclError aclrtMemManagedPrefetchBatchAsync(const void** ptrs, size_t* sizes, size_t count, aclrtMemManagedLocation* prefetchLocs, size_t* prefetchLocIdxs, size_t numPrefetchLocs, uint64_t flags, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptrs | 输入 | 待预取的 UVM 内存地址数组 |
| sizes | 输入 | 预取长度数组 |
| count | 输入 | ptrs/sizes 数组长度 |
| prefetchLocs | 输入 | 物理内存位置数组 |
| prefetchLocIdxs | 输入 | 预取索引数组 |
| numPrefetchLocs | 输入 | 位置数组长度 |
| flags | 输入 | 预留 |
| stream | 输入 | 指定执行预取任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- ptrs/sizes 两数组需等长
- 通过索引数组将不同预取项映射到不同物理位置
