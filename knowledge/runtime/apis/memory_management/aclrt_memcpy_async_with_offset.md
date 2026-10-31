---
type: API
title: aclrtMemcpyAsyncWithOffset
description: "在 Stream 上执行同 Device 内的异步复制，源、目的基址以二级指针传入，并分别指定数据偏移。"
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md
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
- '910'
---
# aclrtMemcpyAsyncWithOffset

## 功能说明

支持基地址为二级指针、有地址偏移的异步内存复制。

## 函数原型

```c
aclError aclrtMemcpyAsyncWithOffset(void **dst, size_t destMax, size_t dstDataOffset, const void **src, size_t count, size_t srcDataOffset, aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| destMax | 输入 | 目的内存最大长度 |
| dstDataOffset | 输入 | 目的内存地址偏移 |
| src | 输入 | 源内存地址指针 |
| count | 输入 | 内存复制长度 |
| srcDataOffset | 输入 | 源内存地址偏移 |
| kind | 输入 | 复制类型，仅支持 ACL_MEMCPY_INNER_DEVICE_TO_DEVICE |
| stream | 输入 | 指定执行任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
