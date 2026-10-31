---
type: API
title: acltdtFreeBuf
description: 释放共享 Buffer。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/17-03_shared_buffer_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_tdt_queue.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/acl_tdt_queue/queue.cpp
  role: implementation
source_headers:
- include/external/acl/acl_tdt_queue.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '310b'
---
# acltdtFreeBuf

## 功能说明

释放共享 Buffer。

## 函数原型

```c
aclError acltdtFreeBuf(acltdtBuf buf)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| buf | 输入 | 待释放的 mbuf。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

仅释放 AllocBuf 申请的 Buffer。
