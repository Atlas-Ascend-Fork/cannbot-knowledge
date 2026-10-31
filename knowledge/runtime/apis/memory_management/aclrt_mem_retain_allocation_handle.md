---
type: API
title: aclrtMemRetainAllocationHandle
description: "从已映射的虚拟地址获取并保留物理内存 handle；每次调用均须配对一次 aclrtFreePhysical。"
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
# aclrtMemRetainAllocationHandle

## 功能说明

根据虚拟内存地址获取物理内存信息的 handle。

## 函数原型

```c
aclError aclrtMemRetainAllocationHandle(void* virPtr, aclrtDrvMemHandle *handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtr | 输入 | 已映射的虚拟内存地址 |
| handle | 输出 | 物理内存信息 handle |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 多次调用需相应调用等次数 [aclrtFreePhysical](aclrt_free_physical.md) 释放
