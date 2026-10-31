---
type: API
title: aclrtGetErrorVerbose
description: 在发生设备故障后获取详细错误信息。必须在获取故障事件之后、提交任务中止之前调用。试验特性。
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
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
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

# aclrtGetErrorVerbose

## 功能说明

在发生设备故障后获取详细错误信息。必须在获取故障事件之后、提交任务中止之前调用。试验特性。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtsGetErrorVerbose(rtsDeviceId, &rtsErrorInfo)` 到 RTS 层；完成 aclrtErrorType 与 rtErrType 的类型转换填充。

## 函数原型

```c
aclError aclrtGetErrorVerbose(int32_t deviceId, aclrtErrorInfo *errorInfo)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID。 |
| errorInfo | 输出 | 错误信息结构体。包含 tryRepair/hasDetail/errorType/detail 等字段。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

- 本接口为试验特性，后续版本可能变更，不支持应用于生产环境中。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L25)
- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L31)
