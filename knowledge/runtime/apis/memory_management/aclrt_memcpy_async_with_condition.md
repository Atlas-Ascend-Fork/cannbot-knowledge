---
type: API
title: aclrtMemcpyAsyncWithCondition
description: 废弃接口，功能等同于 aclrtMemcpyAsync。
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
- topic.quality.compatibility.deprecation
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMemcpyAsyncWithCondition

## 功能说明

废弃接口，功能等同于 [aclrtMemcpyAsync](aclrt_memcpy_async.md)。

## 函数原型

```c
aclError aclrtMemcpyAsyncWithCondition(void *dst, size_t destMax, const void *src, size_t count, aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| destMax | 输入 | 目的内存最大长度，单位 Byte |
| src | 输入 | 源内存地址指针 |
| count | 输入 | 内存复制的长度，单位 Byte |
| kind | 输入 | 内存复制类型 |
| stream | 输入 | 指定执行复制任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 此接口后续版本会废弃，请使用 [aclrtMemcpyAsync](aclrt_memcpy_async.md)
