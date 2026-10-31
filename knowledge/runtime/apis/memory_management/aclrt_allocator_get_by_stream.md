---
type: API
title: aclrtAllocatorGetByStream
description: "按注册时的 Stream 查询自定义 Allocator，返回描述符、对象及分配、释放、建议地址分配和取地址回调。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-08_custom_memory_allocator.md
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
- '950'
- a3
- a2
- '310p'
- '910'
---
# aclrtAllocatorGetByStream

## 功能说明

根据 Stream 查询用户注册的 Allocator 信息。

## 函数原型

```c
aclError aclrtAllocatorGetByStream(aclrtStream stream, aclrtAllocatorDesc *allocatorDesc, aclrtAllocator *allocator, aclrtAllocatorAllocFunc *allocFunc, aclrtAllocatorFreeFunc *freeFunc, aclrtAllocatorAllocAdviseFunc *allocAdviseFunc, aclrtAllocatorGetAddrFromBlockFunc *getAddrFromBlockFunc)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 注册时使用的 Stream |
| allocatorDesc | 输出 | Allocator 描述符指针 |
| allocator | 输出 | 用户提供的 Allocator 对象指针 |
| allocFunc | 输出 | 申请内存 block 的回调函数 |
| freeFunc | 输出 | 释放内存 block 的回调函数 |
| allocAdviseFunc | 输出 | 根据建议地址申请 block 的回调函数 |
| getAddrFromBlockFunc | 输出 | 从 block 获取 Device 地址的回调函数 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/allocator/0_custom_allocator/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/allocator/0_custom_allocator/main.cpp#L107)
