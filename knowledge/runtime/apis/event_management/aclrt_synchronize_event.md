---
type: API
title: aclrtSynchronizeEvent
description: "阻塞 Host 当前线程，等待 Event 记录点捕获的任务完成；仅需轮询时可用 QueryEventStatus。"
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
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtSynchronizeEvent

## 功能说明

阻塞当前线程运行，直到 Event 捕获的所有任务都执行完成。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventSynchronize(event)` 到 RTS 层。

## 函数原型

```c
aclError aclrtSynchronizeEvent(aclrtEvent event)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 需等待的 Event。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L59)
- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L62)
- [`2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp#L44)

## 配套 API 与常见组合

- [aclrtRecordEvent](aclrt_record_event.md)——本接口等待该 Event 记录点之前在其 Stream 上的任务完成
- [aclrtSynchronizeEventWithTimeout](aclrt_synchronize_event_with_timeout.md)——需要防止无限阻塞时，用带超时的变体替代
- [aclrtQueryEventStatus](aclrt_query_event_status.md)——只需非阻塞查询 Event 是否完成而非等待时，改用该接口
