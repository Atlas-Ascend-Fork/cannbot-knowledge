---
type: API
title: aclrtCreateEventExWithFlag
description: "创建资源不受硬件数量限制的 Event，可用于计时、同步或 IPC；不支持 ResetEvent 和 QueryEventWaitStatus。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.cross_process
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

# aclrtCreateEventExWithFlag

## 功能说明

创建带 flag 的 Event，Event 资源不受硬件数量限制。支持 ACL_EVENT_TIME_LINE、ACL_EVENT_SYNC、ACL_EVENT_CAPTURE_STREAM_PROGRESS、ACL_EVENT_IPC。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventCreateExWithFlag(event, flag)` 到 RTS 层；若 RTS 不支持，ACL 层以 WARN_NOT_SUPPORT 处理。

## 函数原型

```c
aclError aclrtCreateEventExWithFlag(aclrtEvent *event, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输出 | Event 的指针。 |
| flag | 输入 | Event flag（bitmap）。支持 ACL_EVENT_TIME_LINE(0x08)、ACL_EVENT_SYNC(0x01)、ACL_EVENT_CAPTURE_STREAM_PROGRESS(0x02)、ACL_EVENT_IPC(0x40)。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 本接口创建的 Event 不支持 [aclrtResetEvent](aclrt_reset_event.md)、aclrtQueryEvent（deprecated）、[aclrtQueryEventWaitStatus](aclrt_query_event_wait_status.md)。
- ACL_EVENT_IPC 不支持与其他 flag 位或；950DT 不支持 ACL_EVENT_IPC。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp#L39)
- [`2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_a.cpp#L79)
- [`2_advanced_features/model_ri/4_model_sync_external/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/4_model_sync_external/main.cpp#L42)
