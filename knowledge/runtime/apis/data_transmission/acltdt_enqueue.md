---
type: API
title: acltdtEnqueue
description: "将 AllocBuf 创建的共享 Buffer 放入队列，支持阻塞、非阻塞及毫秒超时；固定来源版本尚无支持产品。"
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
platforms: []
---
# acltdtEnqueue

## 功能说明

向队列添加共享 Buffer 数据。

## 函数原型

```c
aclError acltdtEnqueue(uint32_t qid, acltdtBuf buf, int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| qid | 输入 | 队列 ID。 |
| buf | 输入 | 共享 Buffer。须 AllocBuf 申请。 |
| timeout | 输入 | -1 阻塞，0 非阻塞，>0 毫秒。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

所有平台均不支持（当前版本无产品落地）。
