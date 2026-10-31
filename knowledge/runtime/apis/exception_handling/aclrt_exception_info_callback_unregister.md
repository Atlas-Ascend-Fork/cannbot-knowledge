---
type: API
title: aclrtExceptionInfoCallbackUnregister
description: 注销通过 aclrtExceptionInfoCallbackRegister 注册的进程级异常回调函数。
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

# aclrtExceptionInfoCallbackUnregister

## 功能说明

注销通过 [aclrtExceptionInfoCallbackRegister](aclrt_exception_info_callback_register.md) 注册的进程级异常回调函数。

## 函数原型

```c
aclError aclrtExceptionInfoCallbackUnregister(aclrtExceptionInfoCallback callback)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| callback | 输入 | 待注销的回调函数，不能为NULL。注销未注册的callback时不执行操作并返回成功。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

进程内任意调用方只要持有相同函数指针均可注销。本接口不等待在途回调结束。
