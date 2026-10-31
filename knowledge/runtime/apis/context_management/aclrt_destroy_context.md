---
type: API
title: aclrtDestroyContext
description: "销毁显式创建的 Context，调用前须同步其 Stream；默认 Context 应通过 aclrtResetDevice 释放。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/05_context_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/context.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_context.cc
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

# aclrtDestroyContext

## 功能说明

销毁通过 [aclrtCreateContext](aclrt_create_context.md) 创建的 Context。不能销毁默认 Context。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtCtxDestroyEx(context)` 到 RTS 层；RTS 内部递减 Context 引用计数，归零时释放底层资源。

## 函数原型

```c
aclError aclrtDestroyContext(aclrtContext context)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| context | 输入 | 待销毁的 Context。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 只能销毁通过 [aclrtCreateContext](aclrt_create_context.md) 显式创建的 Context。默认 Context 通过 [aclrtResetDevice](../device_management/aclrt_reset_device.md) 释放。
- 销毁前需确保该 Context 下的 Stream 已同步完成。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/context/0_context_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/context/0_context_query/main.cpp#L26)
- [`1_basic_features/event/0_event_status/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/0_event_status/main.cpp#L69)
- [`1_basic_features/event/1_event_timestamp/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/event/1_event_timestamp/main.cpp#L92)
