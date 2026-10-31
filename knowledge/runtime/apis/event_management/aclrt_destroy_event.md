---
type: API
title: aclrtDestroyEvent
description: "销毁 Event，无需阻塞等待其任务完成，资源完成后延迟释放；调用时须确保其他接口不再使用该 Event。"
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

# aclrtDestroyEvent

## 功能说明

销毁 Event。支持在 Event 未完成前调用，不会阻塞等待，Event 资源在完成时自动释放。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventDestroy(event)` 到 RTS 层；RTS 标记 Event 为销毁状态，资源延迟释放。

## 函数原型

```c
aclError aclrtDestroyEvent(aclrtEvent event)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待销毁的 Event。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 销毁时需确保其他接口未使用该 Event。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L67)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L89)
- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L76)
