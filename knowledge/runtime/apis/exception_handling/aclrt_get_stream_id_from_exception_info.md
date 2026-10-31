---
type: API
title: aclrtGetStreamIdFromExceptionInfo
description: 获取异常信息中的Stream ID。在异常回调函数中调用，读取 aclrtExceptionInfo 结构体中的 Stream ID 字段。
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

# aclrtGetStreamIdFromExceptionInfo

## 功能说明

获取异常信息中的Stream ID。在异常回调函数中调用，读取 aclrtExceptionInfo 结构体中的 Stream ID 字段。

## 函数原型

```c
uint32_t aclrtGetStreamIdFromExceptionInfo(const aclrtExceptionInfo *info)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| info | 输入 | 异常信息的指针。由Runtime传入，仅在本次回调执行期间有效。 |

## 返回值说明

返回异常信息中的Stream ID。返回0xFFFFFFFF时表示Device异常。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L85)
