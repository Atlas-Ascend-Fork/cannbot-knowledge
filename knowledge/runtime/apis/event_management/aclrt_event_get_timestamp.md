---
type: API
title: aclrtEventGetTimestamp
description: "获取 Event 完成时相对 AI 处理器系统启动的时间戳，单位微秒；须先 Record 并同步 Stream。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.performance.analysis
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

# aclrtEventGetTimestamp

## 功能说明

获取 Event 的执行结束时间点（从 AI 处理器系统启动以来的时间，单位为微秒）。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventGetTimeStamp(timestamp, event)` 到 RTS 层。

## 函数原型

```c
aclError aclrtEventGetTimestamp(aclrtEvent event, uint64_t *timestamp)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 查询的 Event。 |
| timestamp | 输出 | 执行结束时间点（微秒）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 需先 Record Event 并调用 [aclrtSynchronizeStream](../stream_management/aclrt_synchronize_stream.md) 确保任务完成。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L59)
