---
type: API
title: aclrtBinarySetExceptionCallback
description: 注册回调函数，算子执行异常时触发。若多次设置以最后一次为准。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.implementation.callback
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
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtBinarySetExceptionCallback

## 功能说明

注册回调函数，算子执行异常时触发。若多次设置以最后一次为准。

## 函数原型

```c
aclError aclrtBinarySetExceptionCallback(aclrtBinHandle binHandle, aclrtOpExceptionCallback callback, void *userData)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binHandle | 输入 | 算子二进制句柄。 |
| callback | 输入 | 回调函数。原型：typedef void (*aclrtOpExceptionCallback)(aclrtExceptionInfo*exceptionInfo, void *userData) |
| userData | 输入 | 用户数据指针。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
