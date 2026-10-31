---
type: API
title: aclrtIpcOpenEventHandle
description: "导入 aclrtIpcGetEventHandle 导出的共享句柄，取得当前进程可使用的 Event 指针，用于跨进程同步。"
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

# aclrtIpcOpenEventHandle

## 功能说明

在本进程中获取 IPC Event handle 的信息，并返回本进程可用的 Event 指针。需先调用 [aclrtIpcGetEventHandle](aclrt_ipc_get_event_handle.md) 获取 handle。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtIpcOpenEventHandle(handle, &rtEvent)` 到 RTS 层；ACL 层将 rtEvent 转换为 aclrtEvent。

## 函数原型

```c
aclError aclrtIpcOpenEventHandle(aclrtIpcEventHandle handle, aclrtEvent *event)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | IPC Event 句柄。需先通过 [aclrtIpcGetEventHandle](aclrt_ipc_get_event_handle.md) 获取。 |
| event | 输出 | Event 指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950PR、A3、A2 支持；950DT 不支持。
- 310p、310b、910 不支持。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp#L60)
- [`2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/1_ipcevent_multi_device/proc_b.cpp#L65)
