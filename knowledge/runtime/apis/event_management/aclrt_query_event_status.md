---
type: API
title: aclrtQueryEventStatus
description: "非阻塞查询 Event 已捕获任务是否完成，返回 COMPLETE 或 NOT_READY；用于轮询记录点的执行状态。"
tags:
- task.lookup
- topic.implementation.resource_query
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

# aclrtQueryEventStatus

## 功能说明

查询该 Event 捕获的所有任务的执行状态。完成返回 ACL_EVENT_RECORDED_STATUS_COMPLETE，否则返回 ACL_EVENT_RECORDED_STATUS_NOT_READY。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventQueryStatus(event, &rtStatus)` 到 RTS 层。RT_EVENT_RECORDED→ACL_EVENT_RECORDED_STATUS_COMPLETE，其他→ACL_EVENT_RECORDED_STATUS_NOT_READY。

## 函数原型

```c
aclError aclrtQueryEventStatus(aclrtEvent event, aclrtEventRecordedStatus *status)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待查询的 Event。 |
| status | 输出 | Event 状态（aclrtEventRecordedStatus）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 多线程下 Record 和 Query 的乱序可能导致状态不符合预期。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L42)
- [`2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_a.cpp#L49)
- [`2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/ipcevent/0_ipcevent/proc_b.cpp#L79)
