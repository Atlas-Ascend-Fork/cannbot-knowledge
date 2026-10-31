---
type: API
title: aclrtDestroyStreamForce
description: 强制销毁 Stream，不等待任务完成。
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtDestroyStreamForce

## 功能说明

销毁通过 [aclrtCreateStream](aclrt_create_stream.md) 或 [aclrtCreateStreamWithConfig](aclrt_create_stream_with_config.md) 创建的 Stream。若 Stream 上有未完成的任务，直接强制销毁，不等待。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtStreamDestroyForce(stream)` 到 RTS 层；RTS 立即释放 Stream 内部资源，已下发但未完成的任务可能产生未定义行为。

## 函数原型

```c
aclError aclrtDestroyStreamForce(aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 待销毁的 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 需确保该 Stream 在当前 Context 下。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L68)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L91)
- [`1_basic_features/memory/0_h2h_memory_copy/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/0_h2h_memory_copy/main.cpp#L51)
