---
type: API
title: aclrtStreamWaitEvent
description: "向 Stream 异步下发 Event 等待任务，建立跨流依赖；可由多个 Stream 等待同一 Event，超时另由进程级接口配置。"
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
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
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

# aclrtStreamWaitEvent

## 功能说明

阻塞指定 Stream 的运行，直到指定的 Event 完成。异步接口。支持多个 Stream 等待同一个 Event。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamWaitEvent(stream, event)` 到 RTS 层。

## 函数原型

```c
aclError aclrtStreamWaitEvent(aclrtStream stream, aclrtEvent event)
```

本卡记录 `acl_rt.h` 中的双参数 C 接口；带 `timeout` 参数的 [C++ 封装接口](../cpp_extension_apis/aclrt_stream_wait_event.md)调用的是 `aclrtStreamWaitEventWithTimeout`。

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。 |
| event | 输入 | 需等待的 Event。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 可在 `aclInit` 初始化后通过 [aclrtSetOpWaitTimeout](aclrt_set_op_wait_timeout.md) 设置等待超时；超时由后续同步等待接口报告。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L55)
- [`2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp#L64)
- [`2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_b.cpp#L69)

## 配套 API 与常见组合

- [aclrtRecordEvent](aclrt_record_event.md)——本接口等待的是另一 Stream 上被记录的 Event，二者配对实现跨流依赖
- [aclrtQueryEventWaitStatus](aclrt_query_event_wait_status.md)——非阻塞查询本接口产生的等待任务是否已完成
