---
type: API
title: aclrtMemGetAddressRange
description: 获取待查询地址所属内存块的起始地址和大小。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-04_virtual_memory_management.md
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
# aclrtMemGetAddressRange

## 功能说明

获取待查询地址所属内存块的起始地址和大小。

## 函数原型

```c
aclError aclrtMemGetAddressRange(void *ptr, void **pbase, size_t *psize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 待查询的内存地址 |
| pbase | 输出 | 所属内存块的起始地址 |
| psize | 输出 | 所属内存块的大小，单位 Byte |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 支持 [aclrtMalloc](aclrt_malloc.md)、[aclrtMallocHost](aclrt_malloc_host.md)、[aclrtReserveMemAddress](aclrt_reserve_mem_address.md)+MapMem 等内存
