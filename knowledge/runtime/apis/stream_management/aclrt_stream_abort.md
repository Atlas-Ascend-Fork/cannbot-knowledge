---
type: API
title: aclrtStreamAbort
description: 停止指定 Stream 上正在执行的任务，丢弃已下发但未执行的任务。
tags:
- task.lookup
- topic.implementation.synchronization
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtStreamAbort

## 功能说明

停止指定 Stream 上正在执行的任务，丢弃已下发但未执行的任务。本接口执行期间，该 Stream 上新下发的任务不再生效。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamAbort(stream)` 到 RTS 层。

## 函数原型

```c
aclError aclrtStreamAbort(aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定待停止任务的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- 不支持 ACL_STREAM_PERSISTENT 类型的 Stream（950）。
- 依赖该 Stream 的其他 Stream 可能卡住；同步等待接口返回 ACL_ERROR_RT_STREAM_ABORT。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/1_stream_with_failure_mode/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/1_stream_with_failure_mode/main.cpp#L121)
