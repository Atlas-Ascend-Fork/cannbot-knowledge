---
type: API
title: aclrtGetMemcpyDescSize
description: "查询当前 Device 内存复制描述符所需字节数，当前仅支持同 Device 内的 INNER_DEVICE_TO_DEVICE 复制。"
tags:
- task.lookup
- topic.implementation.resource_query
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
# aclrtGetMemcpyDescSize

## 功能说明

获取当前 Device 的内存复制描述符占用的内存大小。

## 函数原型

```c
aclError aclrtGetMemcpyDescSize(aclrtMemcpyKind kind, size_t *descSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| kind | 输入 | 内存复制类型，当前仅支持 ACL_MEMCPY_INNER_DEVICE_TO_DEVICE |
| descSize | 输出 | 内存大小，单位 Byte |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
