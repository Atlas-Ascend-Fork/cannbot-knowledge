---
type: API
title: acllogRegisterCallback
description: 注册设备 plog 日志回调函数，支持最多 16 个回调。
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
- '310b'
- '310p'
- '910'
---

# acllogRegisterCallback

## 功能说明

注册设备 plog 日志回调函数。注册后设备侧上报的 plog 在落盘前触发回调。最多支持 16 个回调，回调返回值不影响落盘及其他回调。

## 函数原型

```c
int32_t acllogRegisterCallback(acllogRecordCallback callbackFunc, void *userData, uint32_t outputLogType, acllogCallbackHandle *callbackHandle)
```

## 参数说明

| 参数 | 输入/输出 | 说明 |
| --- | --- | --- |
| callbackFunc | 输入 | 回调函数，不允许 NULL |
| userData | 输入 | 用户自定义数据，触发回调时传回 |
| outputLogType | 输入 | 日志输出类型（OUTPUT_TYPE_DEBUG/RUN/BOTH） |
| callbackHandle | 输出 | 注册成功后返回的回调句柄 |

## 返回值

0：成功；-1：失败。