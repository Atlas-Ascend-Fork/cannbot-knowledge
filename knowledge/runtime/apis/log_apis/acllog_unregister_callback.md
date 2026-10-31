---
type: API
title: acllogUnregisterCallback
description: 取消注册设备 plog 日志回调函数。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/23_log_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/dfx/base/acl_log.h
  role: header
source_headers:
- include/dfx/base/acl_log.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- 'a3'
- 'a2'
---

# acllogUnregisterCallback

## 功能说明

取消注册设备 plog 日志回调函数。取消后对应回调不再被调用。

## 函数原型

```c
int32_t acllogUnregisterCallback(acllogCallbackHandle callback)
```

## 参数说明

| 参数 | 输入/输出 | 说明 |
| --- | --- | --- |
| callback | 输入 | [acllogRegisterCallback](acllog_register_callback.md) 返回的回调句柄 |

## 返回值

0：成功；-1：失败（无效句柄或未注册句柄）。