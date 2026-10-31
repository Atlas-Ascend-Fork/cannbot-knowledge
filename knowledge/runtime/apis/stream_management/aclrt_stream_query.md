---
type: API
title: aclrtStreamQuery
description: "非阻塞查询 Stream 任务是否全部完成，返回 COMPLETE 或 NOT_READY；持久化、Device 专用和 CPU 调度流的状态无业务语义。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
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

# aclrtStreamQuery

## 功能说明

查询指定 Stream 上所有任务的执行状态。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamQuery(stream)` 到 RTS 层。返回 RT_ERROR_NONE→ACL_STREAM_STATUS_COMPLETE；返回 ACL_ERROR_RT_STREAM_NOT_COMPLETE→ACL_STREAM_STATUS_NOT_READY；其他错误透传。

## 函数原型

```c
aclError aclrtStreamQuery(aclrtStream stream, aclrtStreamStatus *status)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | Stream 的指针。 |
| status | 输出 | Stream 上的任务状态（aclrtStreamStatus）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- ACL_STREAM_PERSISTENT、ACL_STREAM_DEVICE_USE_ONLY、ACL_STREAM_CPU_SCHEDULE 类型 Stream 的 status 无实际业务语义。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/0_simple_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/0_simple_stream/main.cpp#L67)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L131)
