---
type: API
title: aclrtAllocatorCreateDesc
description: 创建aclrtAllocatorDesc类型的数据，表示Allocator描述信息，主要用于注册回调函数。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/allocator.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtAllocatorCreateDesc

## 功能说明

创建aclrtAllocatorDesc类型的数据，表示Allocator描述信息，主要用于注册回调函数。

## 函数原型

```c
aclrtAllocatorDesc aclrtAllocatorCreateDesc()
```

## 参数说明

无

## 返回值说明

- 返回aclrtAllocatorDesc类型的指针，表示成功。
- 返回NULL，表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/allocator/0_custom_allocator/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/allocator/0_custom_allocator/main.cpp#L93)
