---
type: API
title: aclrtSubscribeReport
description: 注册处理Stream上回调函数的线程。一个Stream只允许注册一个线程，同一线程可为多个Stream注册。
tags:
- task.lookup
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/12_execution_control.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/callback.cpp
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

# aclrtSubscribeReport

## 功能说明

注册处理Stream上回调函数的线程。一个Stream只允许注册一个线程，同一线程可为多个Stream注册。
## 函数原型

```c
aclError aclrtSubscribeReport(uint64_t threadId, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| threadId | 输入 | 指定线程的ID。 |
| stream | 输入 | 指定Stream。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

同一Device内的多个Stream可注册同一个线程；不支持给同一个Stream注册多个线程。单进程内注册的线程数量最大值为1024，建议控制在32个以下。不同Device上不能指定同一个线程ID。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/callback/2_callback_exception/exception_callback_sample.cpp#L123)
