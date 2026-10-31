---
type: API
title: aclrtMemManagedGetAttr
description: "查询一段 UVM 内存的单个策略属性；范围内属性值不一致时返回无效值，结果缓冲区由调用方提供。"
tags:
- task.lookup
- topic.implementation.resource_query
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
# aclrtMemManagedGetAttr

## 功能说明

查询指定 UVM 内存范围的单个策略属性值。

## 函数原型

```c
aclError aclrtMemManagedGetAttr(aclrtMemManagedRangeAttribute attribute, const void *ptr, size_t size, void *data, size_t dataSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| attribute | 输入 | 待查询的属性 |
| ptr | 输入 | UVM 内存首地址 |
| size | 输入 | 待查询的内存大小 |
| data | 输出 | 查询结果 |
| dataSize | 输入 | 存放结果的内存大小 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 若范围内属性值不一致，结果为无效值
