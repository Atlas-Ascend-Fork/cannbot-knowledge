---
type: API
title: aclrtHostRegister
description: "按 type 将 Host 内存注册为 Device 可访问并直接返回映射指针；所得 Device 地址不能用于 Host 内存复制操作。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-02_host_memory_management.md
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
# aclrtHostRegister

## 功能说明

将 Host 内存映射注册为 Device 可访问的内存地址。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtHostRegisterImpl 调用 rtHostRegister 完成页表注册。

## 函数原型

```c
aclError aclrtHostRegister(void *ptr, uint64_t size, aclrtHostRegisterType type, void **devPtr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | Host 内存地址；内核 5.10 以下必须使用锁页内存，5.10 以上支持非锁页 |
| size | 输入 | 内存大小，单位 Byte |
| type | 输入 | 内存注册类型，见 aclrtHostRegisterType |
| devPtr | 输出 | Host 内存映射成的 Device 内存地址 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 该 Device 地址仅支持在 Device 上访问，不能用于内存复制等 Host 操作
