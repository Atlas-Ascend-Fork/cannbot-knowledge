---
type: API
title: aclrtSetDeviceTaskAbortCallback
description: 注册回调函数，用于在调用 aclrtDeviceTaskAbort 接口前后触发该回调函数。不支持重复注册。
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
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSetDeviceTaskAbortCallback

## 功能说明

注册回调函数，用于在调用 [aclrtDeviceTaskAbort](aclrt_device_task_abort.md) 接口前后触发该回调函数。不支持重复注册。

## 函数原型

```c
aclError aclrtSetDeviceTaskAbortCallback(const char *regName, aclrtDeviceTaskAbortCallback callback, void *args)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| regName | 输入 | 注册名称，保持唯一，不能为空。 |
| callback | 输入 | 回调函数指针。非NULL表示注册，NULL表示取消注册。原型：typedef int32_t (*`aclrtDeviceTaskAbortCallback`)(int32_t deviceId, `aclrtDeviceTaskAbortStage` stage, uint32_t timeout, void*args) |
| args | 输入 | 待传递给回调函数的用户数据指针。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明
