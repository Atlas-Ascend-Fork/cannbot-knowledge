---
type: API
title: aclrtMemMapNoAccess
description: "将虚拟地址绑定到物理内存但不建立可访问页表；随后须调用 MemSetAccess 设置访问权限。"
tags:
- task.lookup
- topic.implementation.memory_management
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
# aclrtMemMapNoAccess

## 功能说明

将虚拟内存映射到物理内存，不建立可访问页表。

## 函数原型

```c
aclError aclrtMemMapNoAccess(void *virPtr, size_t size, size_t offset, aclrtDrvMemHandle handle, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtr | 输入 | 待映射的虚拟内存地址指针 |
| size | 输入 | 需与 [aclrtMallocPhysical](aclrt_malloc_physical.md) 的 size 相同 |
| offset | 输入 | 物理内存偏移值，当前只能设置为 0 |
| handle | 输入 | 物理内存信息 handle |
| flags | 输入 | 预留，当前只能设置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 映射后目标 Device 上尚未建立可访问页表，需先调用 [aclrtMemSetAccess](aclrt_mem_set_access.md)
