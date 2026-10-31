---
type: API
title: acltdtAllocBuf
description: "申请共享 Buffer，数据区最大 4GB，使用后需 FreeBuf 释放；仅 Atlas 200I/500 A2 的 RC 形态支持。"
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
# acltdtAllocBuf

## 功能说明

申请共享 Buffer 内存。

## 函数原型

```c
aclError acltdtAllocBuf(size_t size, uint32_t type, acltdtBuf *buf)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| size | 输入 | 数据区大小（Byte），≤ 4GB。 |
| type | 输入 | ACL_TDT_NORMAL_MEM（当前仅支持）。 |
| buf | 输出 | 共享 Buffer。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

仅 Atlas 200I/500 A2 RC 形态。需 FreeBuf 释放。
