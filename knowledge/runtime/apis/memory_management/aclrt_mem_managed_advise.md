---
type: API
title: aclrtMemManagedAdvise
description: "对 MemAllocManaged 分配的 UVM 范围设置或取消策略属性，并指定物理位置；操作长度须按 2MB 对齐。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-05_unified_addressing.md
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
- a3
- a2
---
# aclrtMemManagedAdvise

## 功能说明

管理 UVM 内存的策略属性，支持设置和取消。

## 函数原型

```c
aclError aclrtMemManagedAdvise(const void *const ptr, uint64_t size, aclrtMemManagedAdviseType advise, aclrtMemManagedLocation location)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | UVM 内存地址，范围 [0x90000000000, 0x90000000000+3TB) |
| size | 输入 | 内存大小，2MB 对齐 |
| advise | 输入 | 策略属性 |
| location | 输入 | 物理内存位置 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 操作的内存必须是 [aclrtMemAllocManaged](aclrt_mem_alloc_managed.md) 申请的
