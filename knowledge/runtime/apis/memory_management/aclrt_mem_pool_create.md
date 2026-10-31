---
type: API
title: aclrtMemPoolCreate
description: "按配置创建内存池，供后续池内申请与复用；仅 Atlas A2 系列支持，属于不用于生产环境的试验特性。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-10_ordered_stream_memory_allocation.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_memory_soma.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt_memory_soma.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T10:11:53Z'
platforms:
- a2
---
# aclrtMemPoolCreate

## 功能说明

创建内存池。试验特性。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMemPoolCreateImpl 调用 rtMemPoolCreate 创建。

## 函数原型

```c
aclError aclrtMemPoolCreate(aclrtMemPool *memPool, const aclrtMemPoolProps *poolProps)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| memPool | 输出 | 内存池实例 |
| poolProps | 输入 | 内存池配置 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅 Atlas A2 系列支持
- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。
