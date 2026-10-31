---
type: API
title: aclrtMemGetAccess
description: "查询指定虚拟地址在给定内存位置 location 上的访问保护标志，返回权限而非物理内存属性。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.data_movement.memory_access
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMemGetAccess

## 功能说明

获取虚拟内存的访问权限。

## 函数原型

```c
aclError aclrtMemGetAccess(void *virPtr, aclrtMemLocation *location, uint64_t *flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtr | 输入 | 虚拟内存起始地址 |
| location | 输入 | 内存所在位置 |
| flag | 输出 | 内存访问保护标志 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
