---
type: API
title: aclrtRecordEventWithFlag
description: "记录 Stream 的 Event 完成点并指定 flag；EXTERNAL 用于图捕获场景，DEFAULT 沿用普通 Record 行为。"
tags:
- task.lookup
- topic.implementation.synchronization
- topic.graph_execution
- topic.implementation.api_layer.c_api
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
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtRecordEventWithFlag

## 功能说明

在指定 Stream 中记录一个 Event。在 [aclrtRecordEvent](aclrt_record_event.md) 基础上支持 flag，用于图捕获场景（ACL_EVENT_RECORD_EXTERNAL）。

内部行为 （固定 commit `b523035a` 源码结论）：

- flag=ACL_EVENT_RECORD_DEFAULT 时直接调用 `aclrtRecordEventImpl`；flag=ACL_EVENT_RECORD_EXTERNAL 时委托 `rtEventRecordWithFlag(event, stream, flag)` 到 RTS 层。

## 函数原型

```c
aclError aclrtRecordEventWithFlag(aclrtEvent event, aclrtStream stream, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| event | 输入 | 待记录的 Event。 |
| stream | 输入 | 指定 Stream。 |
| flag | 输入 | 记录动作行为：ACL_EVENT_RECORD_DEFAULT(0x00) 或 ACL_EVENT_RECORD_EXTERNAL(0x01)。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- ACL_EVENT_RECORD_EXTERNAL 仅图捕获场景使用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/4_model_sync_external/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/4_model_sync_external/main.cpp#L104)
