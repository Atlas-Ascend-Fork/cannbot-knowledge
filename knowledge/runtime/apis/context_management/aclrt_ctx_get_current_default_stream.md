---
type: API
title: aclrtCtxGetCurrentDefaultStream
description: "获取当前 Context 隐式创建的默认 Stream；当前线程须已有有效 Context，不另建 Stream。"
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

# aclrtCtxGetCurrentDefaultStream

## 功能说明

获取当前 Context 上的默认 Stream。默认 Stream 在 [aclrtSetDevice](../device_management/aclrt_set_device.md) 或 [aclrtCreateContext](aclrt_create_context.md) 时隐式创建。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsCtxGetCurrentDefaultStream(stream)`（即 `rtCtxGetCurrentDefaultStream`）到 RTS 层读取当前 Context 的默认 Stream 句柄。
- 若当前线程无有效 Context，RTS 返回错误。

## 函数原型

```c
aclError aclrtCtxGetCurrentDefaultStream(aclrtStream *stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输出 | 获取到的默认 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 需当前线程已有有效 Context。
- IPV350 不支持默认 Stream。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/context/0_context_query/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/context/0_context_query/main.cpp#L69)
