---
type: API
title: aclrtGetHardwareSyncAddr
description: 获取Cube Core、Vector Core之间的同步地址。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/14_Kernel_loading_and_execution.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtGetHardwareSyncAddr

## 功能说明

获取Cube Core、Vector Core之间的同步地址。

## 函数原型

```c
aclError aclrtGetHardwareSyncAddr(void **addr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| addr | 输出 | 同步地址。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsGetHardwareSyncAddr(addr)` 到 RTS 层。
