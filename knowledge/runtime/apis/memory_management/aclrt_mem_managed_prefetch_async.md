---
type: API
title: aclrtMemManagedPrefetchAsync
description: "在指定 Stream 上预取单段 UVM 到目标物理位置，长度须 2MB 对齐；调用后需同步等待预取完成。"
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
# aclrtMemManagedPrefetchAsync

## 功能说明

异步预取 UVM 内存到指定位置。

## 函数原型

```c
aclError aclrtMemManagedPrefetchAsync(const void* ptr, size_t size, aclrtMemManagedLocation location, uint32_t flags, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 待预取的 UVM 内存地址 |
| size | 输入 | 预取长度，2MB 对齐 |
| location | 输入 | 物理内存位置 |
| flags | 输入 | 预留，固定配置为 0 |
| stream | 输入 | 指定执行预取任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 异步接口，需调用 [aclrtSynchronizeStream](../stream_management/aclrt_synchronize_stream.md) 等待完成
