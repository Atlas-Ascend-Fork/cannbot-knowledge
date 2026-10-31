---
type: API
title: aclrtMemcpyAsyncWithDesc
description: "使用预先设置的复制描述符在 Stream 上异步复制，仅支持同 Device 内复制；先查询描述符大小，再调用 SetMemcpyDesc。"
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
- 'a3'
- 'a2'
- '310b'
---
# aclrtMemcpyAsyncWithDesc

## 功能说明

使用内存复制描述符进行异步内存复制。

## 函数原型

```c
aclError aclrtMemcpyAsyncWithDesc(void *desc, aclrtMemcpyKind kind, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| desc | 输入 | 已通过 [aclrtSetMemcpyDesc](aclrt_set_memcpy_desc.md) 设置的内存复制描述符地址 |
| kind | 输入 | 复制类型，仅支持 ACL_MEMCPY_INNER_DEVICE_TO_DEVICE |
| stream | 输入 | 指定执行复制任务的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 需依次调用 [aclrtGetMemcpyDescSize](aclrt_get_memcpy_desc_size.md) -> [aclrtSetMemcpyDesc](aclrt_set_memcpy_desc.md) -> 本接口
