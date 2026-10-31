---
type: API
title: aclrtReserveMemAddressNoUCMemory
description: "由用户指定起始地址预留不支持 UC 的虚拟内存，不能自动分配地址；大小须为 1GB 的整数倍，最少 1GB。"
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
- a3
---
# aclrtReserveMemAddressNoUCMemory

## 功能说明

预留虚拟内存，不支持 UC 内存。

## 函数原型

```c
aclError aclrtReserveMemAddressNoUCMemory(void **virPtr, size_t size, size_t alignment, void *expectPtr, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtr | 输出 | 已分配的虚拟内存地址的指针的指针 |
| size | 输入 | 虚拟内存大小，1GB 整数倍，最小 1GB |
| alignment | 输入 | 预留，当前只能设置为 0 |
| expectPtr | 输入 | 由用户指定起始地址，建议在 40T-224T 范围内 |
| flags | 输入 | 预留参数 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 虚拟内存起始地址不支持系统自动分配，只能由用户指定
