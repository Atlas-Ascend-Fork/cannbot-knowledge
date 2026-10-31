---
type: API
title: acltdtGetBufDataLen
description: "读取共享 Buffer 已设置的有效数据字节数；未调用 SetBufDataLen 时为 0，与数据区容量区分。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
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
# acltdtGetBufDataLen

## 功能说明

获取有效数据长度。

## 函数原型

```c
aclError acltdtGetBufDataLen(acltdtBuf buf, size_t *len)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| buf | 输入 | Buffer。须 AllocBuf 或 CopyBufRef 申请。 |
| len | 输出 | 有效数据长度（Byte）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

未 SetBufDataLen 时长度为 0。
