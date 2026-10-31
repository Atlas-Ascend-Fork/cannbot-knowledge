---
type: API
title: aclrtMallocForTaskScheduler
description: "申请 Task 调度器可访问的 Device 内存，供图模式下需要此内存类型的算子使用，可指定分配策略和 cfg。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMallocForTaskScheduler

## 功能说明

申请 AI 处理器上 Task 调度器可使用的内存。

## 函数原型

```c
aclError aclrtMallocForTaskScheduler(void **devPtr, size_t size, aclrtMemMallocPolicy policy, aclrtMallocConfig *cfg)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | Device 上已分配内存的指针的指针 |
| size | 输入 | 申请内存的大小，单位 Byte，不能为 0 |
| policy | 输入 | 内存分配规则 |
| cfg | 输入 | 内存配置信息，不指定时传 NULL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 图模式下部分算子需要使用该类型的内存
