---
type: API
title: aclrtExceptionInfoCallbackRegister
description: 注册进程级异常回调函数。支持注册多个不同函数指针的回调函数，与废弃接口可共存。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.implementation.callback
- topic.implementation.api_layer.c_api
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

# aclrtExceptionInfoCallbackRegister

## 功能说明

注册进程级异常回调函数。支持注册多个不同函数指针的回调函数，与废弃接口可共存。

## 函数原型

```c
aclError aclrtExceptionInfoCallbackRegister(aclrtExceptionInfoCallback callback)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| callback | 输入 | 指定要注册的回调函数，不能为NULL。函数原型：typedef void (*aclrtExceptionInfoCallback)(aclrtExceptionInfo *exceptionInfo)。 |

## 返回值说明

返回0表示成功，返回其他值表示失败。入参为NULL时返回参数错误。

## 约束说明

回调函数不应调用资源申请/释放、Stream同步、Device同步等接口。exceptionInfo 仅在本次回调期间有效。Runtime 不保证回调在不同线程间的执行隔离性。
