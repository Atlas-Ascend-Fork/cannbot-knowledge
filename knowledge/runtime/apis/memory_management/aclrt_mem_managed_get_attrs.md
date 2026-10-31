---
type: API
title: aclrtMemManagedGetAttrs
description: "对同一 UVM 地址范围批量查询多个策略属性，按属性数组分别提供结果缓冲区及其大小。"
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
# aclrtMemManagedGetAttrs

## 功能说明

一次查询多个 UVM 内存策略属性值。

## 函数原型

```c
aclError aclrtMemManagedGetAttrs(aclrtMemManagedRangeAttribute *attributes, size_t numAttributes, const void *ptr, size_t size, void **data, size_t *dataSizes)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| attributes | 输入 | 待查询的属性数组 |
| numAttributes | 输入 | 属性数组大小 |
| ptr | 输入 | UVM 内存首地址 |
| size | 输入 | 待查询的内存大小 |
| data | 输出 | 查询结果数组 |
| dataSizes | 输入 | 存放结果的内存大小 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 与 [aclrtMemManagedGetAttr](aclrt_mem_managed_get_attr.md) 的区别在于支持一次查询多个属性
