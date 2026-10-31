---
type: API
title: aclrtStreamStop
description: "停止 Stream 正在执行的任务，保留尚未执行的任务；不支持默认流或已绑定模型的 Stream。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtStreamStop

## 功能说明

仅停止指定 Stream 上的正在执行的任务，不清理任务。与 [aclrtStreamAbort](aclrt_stream_abort.md) 不同，本接口不丢弃已下发未执行的任务。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsStreamStop(stream)` 到 RTS 层。

## 函数原型

```c
aclError aclrtStreamStop(aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定待停止任务的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- 不支持默认 Stream（stream=NULL）。
- 不支持与模型绑定过的 Stream。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/1_stream_with_failure_mode/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/1_stream_with_failure_mode/main.cpp#L95)
