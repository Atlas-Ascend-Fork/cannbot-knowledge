---
type: API
title: aclrtCreateEventWithFlag
description: "按 flag 创建计时、同步或进度捕获 Event；后续使用 ResetEvent 或 StreamWaitEvent 时须包含 ACL_EVENT_SYNC。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtCreateEventWithFlag

## 功能说明

创建带 flag 的 Event，支持同时使能多个 flag（按位或）。flag 包括 ACL_EVENT_TIME_LINE、ACL_EVENT_SYNC、ACL_EVENT_CAPTURE_STREAM_PROGRESS、ACL_EVENT_EXTERNAL、ACL_EVENT_DEVICE_USE_ONLY。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventCreateWithFlag(event, flag)` 到 RTS 层。

## 函数原型

```c
aclError aclrtCreateEventWithFlag(aclrtEvent *event, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输出 | Event 的指针。 |
| flag | 输入 | Event flag（bitmap）。支持 ACL_EVENT_TIME_LINE(0x08)、ACL_EVENT_SYNC(0x01)、ACL_EVENT_CAPTURE_STREAM_PROGRESS(0x02)、ACL_EVENT_EXTERNAL(0x20)、ACL_EVENT_DEVICE_USE_ONLY(0x10)。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- ACL_EVENT_DEVICE_USE_ONLY 仅 950、A3、A2、310p 支持（310b 不支持）。
- 不包含 ACL_EVENT_SYNC 的 Event 不支持 [aclrtResetEvent](aclrt_reset_event.md) 和 [aclrtStreamWaitEvent](aclrt_stream_wait_event.md)。
- ACL_EVENT_EXTERNAL 不支持与其他 flag 位或。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/1_model_update/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/1_model_update/main.cpp#L88)
