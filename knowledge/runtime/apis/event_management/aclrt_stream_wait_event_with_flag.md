---
type: API
title: aclrtStreamWaitEventWithFlag
description: "为 Stream 的 Event 等待指定超时和 flag；图捕获使用 WAIT_EXTERNAL 时，timeout 必须为 0。"
tags:
- task.lookup
- topic.implementation.synchronization
- topic.graph_execution
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
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtStreamWaitEventWithFlag

## 功能说明

阻塞指定 Stream 的运行，直到指定的 Event 完成。在 [aclrtStreamWaitEvent](aclrt_stream_wait_event.md) 和 [aclrtStreamWaitEventWithTimeout](aclrt_stream_wait_event_with_timeout.md) 基础上支持超时和 flag。图捕获场景可使用 ACL_EVENT_WAIT_EXTERNAL。

内部行为 （固定 commit `b523035a` 源码结论）：

- ACL 层校验 flag 为 ACL_EVENT_WAIT_DEFAULT 或 ACL_EVENT_WAIT_EXTERNAL；flag=EXTERNAL 时 timeout 必须为 0。
- 委托 `rtStreamWaitEventWithFlag(stream, event, timeout, flag)` 到 RTS 层。

## 函数原型

```c
aclError aclrtStreamWaitEventWithFlag(aclrtStream stream, aclrtEvent event, uint32_t timeout, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。 |
| event | 输入 | 需等待的 Event。 |
| timeout | 输入 | 超时时间（秒）。flag=WAIT_EXTERNAL 时必须为 0。 |
| flag | 输入 | 等待行为标志：ACL_EVENT_WAIT_DEFAULT(0x00) 或 ACL_EVENT_WAIT_EXTERNAL(0x01)。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- ACL_EVENT_WAIT_EXTERNAL 仅图捕获场景使用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/4_model_sync_external/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/4_model_sync_external/main.cpp#L52)
