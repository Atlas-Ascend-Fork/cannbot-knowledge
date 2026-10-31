---
type: API
title: aclrtEventElapsedTime
description: "计算同一 Stream 中两个 Event 记录点之间的耗时，单位毫秒；须先同步 Stream，确保两者已完成。"
tags:
- task.lookup
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

# aclrtEventElapsedTime

## 功能说明

统计两个 Event 之间的耗时。需配合 [aclrtCreateEvent](aclrt_create_event.md)、[aclrtRecordEvent](aclrt_record_event.md)、[aclrtSynchronizeStream](../stream_management/aclrt_synchronize_stream.md) 使用。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventElapsedTime(ms, startEvent, endEvent)` 到 RTS 层。

## 函数原型

```c
aclError aclrtEventElapsedTime(float *ms, aclrtEvent startEvent, aclrtEvent endEvent)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ms | 输出 | 耗时（毫秒）的指针。 |
| startEvent | 输入 | 起始 Event。 |
| endEvent | 输入 | 结尾 Event。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 需在同一个 Stream 中 Record 起始和结尾 Event，并先调用 [aclrtSynchronizeStream](../stream_management/aclrt_synchronize_stream.md) 确保任务完成。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L63)
