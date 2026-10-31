---
type: API
title: aclrtCreateEvent
description: "创建用于计时或跨 Stream 同步的 Event；首次 Record 才申请硬件资源，可能阻塞，不支持 aclrtResetEvent。"
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

# aclrtCreateEvent

## 功能说明

创建 Event，可用于统计两个 Event 之间的耗时、多 Stream 同步等场景。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventCreate(event)` 到 RTS 层（RTS passthrough 中 rtEventCreate 调用 rtEventCreateWithFlag(evt, RT_EVENT_DEFAULT)）。
- 创建时并不实际申请硬件资源，资源在首次 [aclrtRecordEvent](aclrt_record_event.md) 时按需分配。

## 函数原型

```c
aclError aclrtCreateEvent(aclrtEvent *event)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输出 | Event 的指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 本接口创建的 Event 不支持在 [aclrtResetEvent](aclrt_reset_event.md) 中使用。
- 首次 Record 时可能因等待资源而阻塞。
- Event 最大数：950/A3/A2/310b 为 65536，310p 为 1023，910 为 65535。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L39)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L42)
- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L45)
