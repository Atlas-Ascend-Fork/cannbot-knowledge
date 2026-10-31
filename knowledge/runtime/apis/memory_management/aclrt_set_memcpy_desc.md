---
type: API
title: aclrtSetMemcpyDesc
description: "在 Device 描述符中记录同 Device 复制的源、目的地址和长度；先用 GetMemcpyDescSize 查询大小并申请描述符内存。"
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
# aclrtSetMemcpyDesc

## 功能说明

设置内存复制描述符，记录源地址、目的地址和复制长度。

## 函数原型

```c
aclError aclrtSetMemcpyDesc(void *desc, aclrtMemcpyKind kind, void *srcAddr, void *dstAddr, size_t count, void *config)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| desc | 输出 | 内存复制描述符地址指针，需为 Device 内存 |
| kind | 输入 | 复制类型，仅支持 ACL_MEMCPY_INNER_DEVICE_TO_DEVICE |
| srcAddr | 输入 | 源内存地址指针 |
| dstAddr | 输入 | 目的内存地址指针 |
| count | 输入 | 内存复制长度，单位 Byte |
| config | 输入 | 预留参数，传 NULL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 需先调用 [aclrtGetMemcpyDescSize](aclrt_get_memcpy_desc_size.md) 获取描述符大小并申请 Device 内存
