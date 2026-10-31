---
type: API
title: aclrtKernelArgsGetHandleMemSize
description: "查询指定 Kernel 参数句柄对象所需的存储字节数，供用户管理参数内存时分配句柄空间；参数数据空间另用 GetMemSize 查询。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtKernelArgsGetHandleMemSize

## 功能说明

获取参数列表句柄占用的内存大小。

## 函数原型

```c
aclError aclrtKernelArgsGetHandleMemSize(aclrtFuncHandle funcHandle, size_t *memSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| memSize | 输出 | 参数列表句柄占用内存大小（Byte）。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsKernelArgsGetHandleMemSize(funcHandle, memSize)` 到 RTS 层。
