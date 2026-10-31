---
type: API
title: acltdtCopyBufRef
description: "为共享 Buffer 创建指向同一数据区的新引用，避免复制数据；源 Buffer 须由 AllocBuf 或 CopyBufRef 创建。"
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
# acltdtCopyBufRef

## 功能说明

引用拷贝共享 Buffer 数据区。

## 函数原型

```c
aclError acltdtCopyBufRef(const acltdtBuf buf, acltdtBuf *newBuf)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| buf | 输入 | 源 Buffer。须 AllocBuf 或 CopyBufRef 申请。 |
| newBuf | 输出 | 新 Buffer 指向相同数据区。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

仅 Atlas 200I/500 A2 RC 形态。
