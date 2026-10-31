---
type: API
title: aclrtIpcGetEventHandle
description: "将带 ACL_EVENT_IPC 标志的 Ex Event 导出为跨进程共享句柄，用于同 Device 多进程或跨 Device 的任务同步。"
tags:
- task.lookup
- topic.implementation.cross_process
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
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtIpcGetEventHandle

## 功能说明

将本进程中的指定 Event 设置为 IPC（Inter-Process Communication）Event，并返回其 handle，用于跨进程任务同步。支持同 Device 多进程及跨 Device。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtIpcGetEventHandle(event, handle)` 到 RTS 层；若 RTS 不支持，ACL 层以 WARN_NOT_SUPPORT 处理。

## 函数原型

```c
aclError aclrtIpcGetEventHandle(aclrtEvent event, aclrtIpcEventHandle *handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 指定 Event。仅支持 [aclrtCreateEventExWithFlag](aclrt_create_event_ex_with_flag.md) 创建、flag 为 ACL_EVENT_IPC 的 Event。 |
| handle | 输出 | IPC Event 句柄。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950PR、A3、A2 支持；950DT 不支持。
- 310p、310b、910 不支持。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp#L58)
- [`2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_a.cpp#L97)
