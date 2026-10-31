---
type: API
title: aclrtGetCurrentContext
description: "查询当前线程最后绑定的 Context；线程未设置 Device 或 Context 时，返回的 Context 指针为空。"
tags:
- task.lookup
- topic.implementation.resource_query
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

# aclrtGetCurrentContext

## 功能说明

获取当前线程的 Context。若多次调用 [aclrtSetCurrentContext](aclrt_set_current_context.md)，则获取最后一次设置的 Context。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtCtxGetCurrent(context)` 到 RTS 层读取 TLS 中的当前 Context 句柄。若 TLS 中无有效 Context，RTS 返回错误。

## 函数原型

```c
aclError aclrtGetCurrentContext(aclrtContext *context)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| context | 输出 | 当前线程 Context 的指针。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。TLS 中无 Context 时 `*context` 为 NULL。

## 约束说明

- 若当前线程既未调用 [aclrtSetDevice](../device_management/aclrt_set_device.md) 也未调用 [aclrtCreateContext](aclrt_create_context.md) / [aclrtSetCurrentContext](aclrt_set_current_context.md)，则获取到的 context 为 NULL。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/context/0_context_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/context/0_context_query/main.cpp#L62)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L88)
