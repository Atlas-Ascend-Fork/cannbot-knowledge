---
type: API
title: aclrtMallocAlign32
description: 在 Device 上分配 size 大小的线性内存，仅向上 32 字节对齐（不额外加 32 字节）。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-01_device_memory_malloc_and_free.md
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
# aclrtMallocAlign32

## 功能说明

在 Device 上分配 size 大小的线性内存，仅向上 32 字节对齐（不额外加 32 字节）。

## 函数原型

```c
aclError aclrtMallocAlign32(void **devPtr, size_t size, aclrtMemMallocPolicy policy)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | Device 上已分配内存的指针的指针 |
| size | 输入 | 申请内存的大小，单位 Byte，不能为 0 |
| policy | 输入 | 内存分配规则，见 aclrtMemMallocPolicy；非法值时 size≥2MB 按大页分配 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 分配的内存不会初始化
- policy 仅支持单个枚举项（IPV350 除外）
- 对于 950 功能等同 [aclrtMalloc](aclrt_malloc.md)；对于其他型号只对齐 32 字节不额外加 32 字节
