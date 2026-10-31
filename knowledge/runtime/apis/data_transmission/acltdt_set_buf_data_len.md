---
type: API
title: acltdtSetBufDataLen
description: "设置共享 Buffer 的有效数据字节数，长度须小于 GetBufData 返回的数据区容量，与申请容量区分。"
tags:
- task.lookup
- topic.data_movement.memory_access
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
# acltdtSetBufDataLen

## 功能说明

设置有效数据长度。

## 函数原型

```c
aclError acltdtSetBufDataLen(acltdtBuf buf, size_t len)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| buf | 输入 | Buffer。须 AllocBuf 或 CopyBufRef 申请。 |
| len | 输入 | 有效数据长度（Byte）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

长度须小于 GetBufData 获取的 size。
