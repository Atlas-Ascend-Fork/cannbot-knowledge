---
type: API
title: aclrtDeviceTaskAbort
description: 停止指定Device上正在执行的任务并丢弃已下发未执行的任务。试验特性。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/13_exception_handling.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/device.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-31T02:15:45Z'
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtDeviceTaskAbort

## 功能说明

停止指定Device上正在执行的任务并丢弃已下发未执行的任务。试验特性。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtDeviceTaskAbort(deviceId, timeout)` 到 RTS 层。

## 函数原型

```c
aclError aclrtDeviceTaskAbort(int32_t deviceId, uint32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID。 |
| timeout | 输入 | 超时时间（毫秒）。0表示永久等待；>0表示具体超时时间，最大36分钟。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。

仅支持遇错即停场景。默认模式为遇错继续，需先调用 [aclrtSetStreamFailureMode](../stream_management/aclrt_set_stream_failure_mode.md) 设置遇错即停模式。
