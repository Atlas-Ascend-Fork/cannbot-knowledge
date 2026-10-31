---
type: API
title: aclrtCtxGetFloatOverflowAddr
description: "获取当前 Context 中保存饱和模式溢出标记的 Device 地址，作为 Workspace 参数传给 AI Core 算子。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.precision
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

# aclrtCtxGetFloatOverflowAddr

## 功能说明

饱和模式下，获取保存溢出标记的 Device 内存地址，该地址需作为 Workspace 参数传递给 AI Core 算子。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsCtxGetFloatOverflowAddr(overflowAddr)` 到 RTS 层；返回的地址由 RTS 在当前 Context 的 Device 内存空间中分配维护。

## 函数原型

```c
aclError aclrtCtxGetFloatOverflowAddr(void **overflowAddr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| overflowAddr | 输出 | 保存溢出标记的 Device 内存地址。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 当前线程需有有效 Context。
- IPV350 不支持。
