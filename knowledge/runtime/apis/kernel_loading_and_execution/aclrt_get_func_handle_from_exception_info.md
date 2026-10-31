---
type: API
title: aclrtGetFuncHandleFromExceptionInfo
description: 从 aclrtExceptionInfo 异常信息中获取核函数句柄。配合 aclrtBinarySetExceptionCallback 使用。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
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

# aclrtGetFuncHandleFromExceptionInfo

## 功能说明

从 aclrtExceptionInfo 异常信息中获取核函数句柄。配合 [aclrtBinarySetExceptionCallback](aclrt_binary_set_exception_callback.md) 使用。

## 函数原型

```c
aclError aclrtGetFuncHandleFromExceptionInfo(const aclrtExceptionInfo *info, aclrtFuncHandle *func)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| info | 输入 | 异常信息指针。 |
| func | 输出 | 核函数句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。info为空指针时返回 ACL_ERROR_INVALID_EXCEPTION_INFO。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L102)
