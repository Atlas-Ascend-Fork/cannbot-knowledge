---
type: API
title: acltdtAppendBufChain
description: "将共享 Buffer 接入指定头 Buffer 的链表，用于组织多个数据区；单链表最多 128 个 Buffer。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '310b'
---
# acltdtAppendBufChain

## 功能说明

添加共享 Buffer 到链表。

## 函数原型

```c
aclError acltdtAppendBufChain(acltdtBuf headBuf, acltdtBuf buf)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| headBuf | 输入 | 链表头部 Buffer。 |
| buf | 输入 | 待添加 Buffer。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

链表最大 128 个 Buffer。
