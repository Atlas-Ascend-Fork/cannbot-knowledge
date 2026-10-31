---
type: API
title: aclrtResetEvent
description: "在 Stream 上异步复位 Event 以便复用；仅支持 WithFlag 创建且带 ACL_EVENT_SYNC 的 Event。"
tags:
- task.lookup
- topic.implementation.synchronization
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

# aclrtResetEvent

## 功能说明

复位 Event，恢复 Event 初始状态，便于 Event 对象重复使用。异步接口。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtEventReset(event, stream)` 到 RTS 层。

## 函数原型

```c
aclError aclrtResetEvent(aclrtEvent event, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待复位的 Event。 |
| stream | 输入 | 指定 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅支持复位 [aclrtCreateEventWithFlag](aclrt_create_event_with_flag.md) 创建的、带有 ACL_EVENT_SYNC 标志的 Event。
- 多 Stream 等待同一 Event 时不建议复位。
- IPV350 不支持。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/stream/2_multi_stream/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/stream/2_multi_stream/main.cpp#L58)
- [`2_advanced_features/model_ri/1_model_update/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/1_model_update/main.cpp#L96)
