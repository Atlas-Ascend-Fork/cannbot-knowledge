---
type: API
title: acltdtSetBufUserData
description: "按偏移写入共享 Buffer 的私有数据区，offset+size 不能超过 96 字节，与主数据区写入区分。"
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
# acltdtSetBufUserData

## 功能说明

设置共享 Buffer 私有数据。

## 函数原型

```c
aclError acltdtSetBufUserData(acltdtBuf buf, const void *dataPtr, size_t size, size_t offset)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| buf | 输出 | 共享 Buffer。 |
| dataPtr | 输入 | 用户数据地址。 |
| size | 输入 | 数据长度（Byte），≤ 96。 |
| offset | 输入 | 偏移（Byte），≤ 96。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

私有数据区 96 Byte，offset+size ≤ 96。
