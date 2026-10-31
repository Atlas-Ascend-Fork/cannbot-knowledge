---
type: API
title: aclrtQueryEventWaitStatus
description: "查询 StreamWaitEvent 下发的等待任务是否全部完成；区别于记录点状态查询，不支持 ExWithFlag 创建的 Event。"
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

# aclrtQueryEventWaitStatus

## 功能说明

调用 [aclrtStreamWaitEvent](aclrt_stream_wait_event.md) 后查询该 Event 对应的等待任务是否都执行完成。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventQueryWaitStatus(event, &rtWaitStatus)` 到 RTS 层。EVENT_STATUS_COMPLETE→ACL_EVENT_WAIT_STATUS_COMPLETE，其他→ACL_EVENT_WAIT_STATUS_NOT_READY。

## 函数原型

```c
aclError aclrtQueryEventWaitStatus(aclrtEvent event, aclrtEventWaitStatus *status)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待查询的 Event。 |
| status | 输出 | 等待状态（aclrtEventWaitStatus）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 通过 [aclrtCreateEventExWithFlag](aclrt_create_event_ex_with_flag.md) 创建的 Event 不支持本接口。
- IPV350 不支持。
