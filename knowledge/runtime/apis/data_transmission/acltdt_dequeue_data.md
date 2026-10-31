---
type: API
title: acltdtDequeueData
description: "从队列读取数据及用户数据，返回实际数据字节数；支持阻塞或毫秒超时，timeout=0 的非阻塞仅限 Device。"
tags:
- task.lookup
- topic.data_movement
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/17-02_shared_queue_management.md
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
- '950'
- a3
- a2
- '310b'
- '310p'
- '910'
---
# acltdtDequeueData

## 功能说明

从队列获取数据。

## 函数原型

```c
aclError acltdtDequeueData(uint32_t qid, void *data, size_t dataSize, size_t *retDataSize, void *userData, size_t userDataSize, int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| qid | 输入 | 队列 ID。 |
| data | 输入&输出 | 数据指针。 |
| dataSize | 输入 | 数据大小（Byte）。 |
| retDataSize | 输出 | 实际返回大小。 |
| userData | 输入&输出 | 自定义数据。 |
| userDataSize | 输入 | 自定义数据大小。 |
| timeout | 输入 | -1 阻塞，0 非阻塞（仅 Device），>0 毫秒。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

0 超时仅支持 Device 场景。
