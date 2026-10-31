---
type: API
title: aclrtSetExceptionInfoCallback(deprecated)
description: 设置进程级异常回调函数。已废弃，请使用 aclrtExceptionInfoCallbackRegister / aclrtExceptionInfoCallbackUnregister。若多次设置以最后一次为准。不影响通过 Register 接口注册的回调函数。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.implementation.callback
- topic.implementation.api_layer.c_api
- topic.quality.compatibility.deprecation
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/13_exception_handling.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
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

# aclrtSetExceptionInfoCallback(deprecated)

## 功能说明

设置进程级异常回调函数。已废弃，请使用 [aclrtExceptionInfoCallbackRegister](aclrt_exception_info_callback_register.md) / [aclrtExceptionInfoCallbackUnregister](aclrt_exception_info_callback_unregister.md)。若多次设置以最后一次为准。不影响通过 Register 接口注册的回调函数。

## 函数原型

```c
aclError aclrtSetExceptionInfoCallback(aclrtExceptionInfoCallback callback)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| callback | 输入 | 指定要注册的回调函数。函数原型：typedef void (*aclrtExceptionInfoCallback)(aclrtExceptionInfo *exceptionInfo)。传入NULL可清空回调。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

回调函数不应调用资源申请/释放、Stream同步、Device同步、任务下发、任务终止等接口。exceptionInfo 由 Runtime 管理，仅在本次回调执行期间有效。
