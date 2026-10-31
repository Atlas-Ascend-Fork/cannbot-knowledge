---
type: API
title: aclrtGetFunctionSize
description: 根据核函数句柄获取核函数代码段的大小。
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
platforms:
- '950'
- 'a3'
- 'a2'
- '310p'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtGetFunctionSize

## 功能说明

根据核函数句柄获取核函数代码段的大小。

## 函数原型

```c
aclError aclrtGetFunctionSize(aclrtFuncHandle funcHandle, size_t *aicSize, size_t *aivSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| aicSize | 输出 | AI Core/Cube Core上代码段大小（Byte）。仅Vector Core执行时为0。 |
| aivSize | 输出 | Vector Core上代码段大小（Byte）。仅AI Core/Cube Core执行时为0。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtFuncGetSize(funcHandle, aicSize, aivSize)` 到 RTS 层。
