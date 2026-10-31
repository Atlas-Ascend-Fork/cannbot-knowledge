---
type: API
title: aclrtPeekAtLastError
description: 获取当前线程的Runtime错误码，仅获取但不清空错误码。
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
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/context.cpp
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

# aclrtPeekAtLastError

## 功能说明

获取当前线程的Runtime错误码，仅获取但不清空错误码。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 校验 level 必须为 ACL_RT_THREAD_LEVEL；委托 `rtPeekAtLastError(rtLevel)` 到 RTS 层。

## 函数原型

```c
aclError aclrtPeekAtLastError(aclrtLastErrLevel level)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| level | 输入 | 指定获取错误码的级别，当前仅支持线程级别（ACL_RT_THREAD_LEVEL）。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/1_error_handling/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/1_error_handling/main.cpp#L66)
- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L41)
