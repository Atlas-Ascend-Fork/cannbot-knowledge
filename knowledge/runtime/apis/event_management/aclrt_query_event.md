---
type: API
title: aclrtQueryEvent（废弃）
description: "旧版 Event 完成状态查询，查询同一线程 Record 的 Event；后续版本将废弃，推荐改用 aclrtQueryEventStatus。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
- topic.quality.compatibility.deprecation
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/07_event_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/event.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c.cc
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

# aclrtQueryEvent（废弃）

**须知：此接口后续版本会废弃，请使用 [aclrtQueryEventStatus](aclrt_query_event_status.md) 接口。**

## 功能说明

查询与本接口在同一线程中的 [aclrtRecordEvent](aclrt_record_event.md) 所记录的 Event 是否执行完成。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventQuery(event)` 到 RTS 层。RT_ERROR_NONE→ACL_EVENT_STATUS_COMPLETE；ACL_ERROR_RT_EVENT_NOT_COMPLETE→ACL_EVENT_STATUS_NOT_READY。

## 函数原型

```c
aclError aclrtQueryEvent(aclrtEvent event, aclrtEventStatus *status)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待查询的 Event。 |
| status | 输出 | Event 状态（aclrtEventStatus）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 此接口已废弃，推荐使用 [aclrtQueryEventStatus](aclrt_query_event_status.md)。
- IPV350 不支持。
