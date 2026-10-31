---
type: API
title: aclrtSetOpWaitTimeout
description: "设置进程级后续 StreamWaitEvent 任务的等待超时，单位秒，0 表示不超时；超时由同步等待接口报告。"
tags:
- task.lookup
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/07_event_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_event.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSetOpWaitTimeout

## 功能说明

设置等待 Event 完成的超时时间。不调用则默认不超时；一个进程内多次调用以最后一次为准。设置后，该进程内后续 [aclrtStreamWaitEvent](aclrt_stream_wait_event.md) 下发的任务在超时未完成时通过同步等待接口返回报错。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtSetOpWaitTimeOut(timeout)` 到 RTS 层。

## 函数原型

```c
aclError aclrtSetOpWaitTimeout(uint32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| timeout | 输入 | 超时时间（秒）。0 表示不超时。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 调用本接口前需先调用 [aclInit](../runtime_configuration/acl_init.md)。
- 310p 不支持。
- IPV350 不支持。
