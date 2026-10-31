---
type: API
title: aclrtKernelArgsGetMemSize
description: "根据 Kernel 和用户参数大小查询参数数据实际所需的存储字节数；用户参数逐项按 8 字节对齐后累计，句柄空间另行查询。"
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

# aclrtKernelArgsGetMemSize

## 功能说明

获取Kernel Launch时参数列表所需内存的实际大小。

## 函数原型

```c
aclError aclrtKernelArgsGetMemSize(aclrtFuncHandle funcHandle, size_t userArgsSize, size_t *actualArgsSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| userArgsSize | 输入 | 参数列表数据所需大小（Byte，每个参数8字节对齐后求和）。 |
| actualArgsSize | 输出 | 实际所需内存大小（Byte）。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsKernelArgsGetMemSize(funcHandle, userArgsSize, actualArgsSize)` 到 RTS 层。
