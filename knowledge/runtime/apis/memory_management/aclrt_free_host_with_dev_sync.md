---
type: API
title: aclrtFreeHostWithDevSync
description: 释放 Host 内存，内部会执行隐式 Device 同步。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.synchronization
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtFreeHostWithDevSync

## 功能说明

释放 Host 内存，内部会执行隐式 Device 同步。

## 函数原型

```c
aclError aclrtFreeHostWithDevSync(void *hostPtr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| hostPtr | 输入 | 待释放的 Host 内存指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 内部会执行隐式 Device 同步，等待使用该内存的任务完成
