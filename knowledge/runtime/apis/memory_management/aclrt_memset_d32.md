---
type: API
title: aclrtMemsetD32
description: "以 uint32_t 为单位同步填充内存，N 表示元素数，容量须至少 N×4 字节；不隐式同步 Device。"
tags:
- task.lookup
- topic.data_movement.memory_access
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
- a3
- a2
---
# aclrtMemsetD32

## 功能说明

以 32 位无符号整数为单位同步填充内存。

## 函数原型

```c
aclError aclrtMemsetD32(void *ptr, size_t memSize, uint32_t value, size_t N)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 内存起始地址指针（仅支持 [aclrtMalloc](aclrt_malloc.md) 或 [aclrtMallocHost](aclrt_malloc_host.md) 申请的内存） |
| memSize | 输入 | 内存最大长度，单位 Byte，必须 >= N*4 |
| value | 输入 | 要填充的 32 位无符号整数值 |
| N | 输入 | 32 位无符号整数值的数量 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 同步执行，内部不会隐式 Device 同步
