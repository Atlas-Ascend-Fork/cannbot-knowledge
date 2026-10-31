---
type: API
title: aclrtMemPoolGetAttr
description: 获取内存池指定属性的值。试验特性。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.memory_management
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
# aclrtMemPoolGetAttr

## 功能说明

获取内存池指定属性的值。试验特性。

## 函数原型

```c
aclError aclrtMemPoolGetAttr(aclrtMemPool memPool, aclrtMemPoolAttr attr, void *value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| memPool | 输入 | 内存池实例 |
| attr | 输入 | 指定属性 |
| value | 输出 | 指向输出属性值的指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。
- 未设置属性则返回默认值
