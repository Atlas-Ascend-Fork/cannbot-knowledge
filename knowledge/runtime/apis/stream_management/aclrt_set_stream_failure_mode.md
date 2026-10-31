---
type: API
title: aclrtSetStreamFailureMode
description: "设置任务失败后继续执行或遇错即停，每条 Stream 仅可设置一次；遇错即停会影响同一 Context 下其他流。"
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
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

# aclrtSetStreamFailureMode

## 功能说明

当 Stream 上下发了多个任务时，通过本接口指定任务调度模式，控制某个任务失败后是否继续执行下一个任务。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamSetMode(stream, mode)` 到 RTS 层。mode 取值：ACL_CONTINUE_ON_FAILURE（继续执行）或 ACL_STOP_ON_FAILURE（遇错即停）。

## 函数原型

```c
aclError aclrtSetStreamFailureMode(aclrtStream stream, uint64_t mode)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 待操作 Stream。 |
| mode | 输入 | 任务调度模式：ACL_CONTINUE_ON_FAILURE（默认）或 ACL_STOP_ON_FAILURE（遇错即停）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 每个 Stream 只能调用一次本接口。
- 遇错即停模式下，该 Stream 所在 Context 下的其他 Stream 也是遇错即停。
- 950、A3、A2 支持默认 Stream（stream=NULL）；910、310p、310b 不支持默认 Stream。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L38)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L41)
- [`1_basic_features/stream/0_simple_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/0_simple_stream/main.cpp#L52)
