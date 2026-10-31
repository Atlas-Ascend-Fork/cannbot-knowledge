---
type: API
title: aclrtBinaryGetFunctionByEntry
description: 根据 Function Entry 获取核函数句柄。预留接口，暂不支持。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/14_Kernel_loading_and_execution.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms: []

source_headers:
- include/external/acl/acl_rt.h
---

# aclrtBinaryGetFunctionByEntry

## 功能说明

根据 Function Entry 获取核函数句柄。预留接口，暂不支持。

## 函数原型

```c
aclError aclrtBinaryGetFunctionByEntry(aclrtBinHandle binHandle, uint64_t funcEntry, aclrtFuncHandle *funcHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binHandle | 输入 | 算子二进制句柄。 |
| funcEntry | 输入 | 标识核函数的关键字。 |
| funcHandle | 输出 | 核函数句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
