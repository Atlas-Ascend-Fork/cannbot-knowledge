---
type: API
title: aclrtRecordEvent
description: "在 Stream 上异步记录已下发任务的完成点，配合另一 Stream 的 WaitEvent 建立依赖，或供 Host 同步等待。"
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

# aclrtRecordEvent

## 功能说明

在指定 Stream 中记录一个 Event。异步接口。与 [aclrtStreamWaitEvent](aclrt_stream_wait_event.md) 配合实现多 Stream 同步。会捕获当前 Stream 上已下发的任务记录到 Event 中。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventRecord(event, stream)` 到 RTS 层。

## 函数原型

```c
aclError aclrtRecordEvent(aclrtEvent event, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待记录的 Event。 |
| stream | 输入 | 指定 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 通过 [aclrtCreateEventExWithFlag](aclrt_create_event_ex_with_flag.md) 创建的 Event 支持多次 Record 复用。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L51)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L50)
- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L53)

## 配套 API 与常见组合

- [aclrtCreateEvent](aclrt_create_event.md)——记录前须先创建 Event；用于跨 Stream 同步的 Event 创建方式决定其可用能力
- [aclrtStreamWaitEvent](aclrt_stream_wait_event.md)——另一 Stream 等待本接口记录的 Event，实现跨 Stream 的任务依赖
- [aclrtSynchronizeEvent](aclrt_synchronize_event.md)——Host 侧阻塞等待本接口记录点之前的任务全部完成
