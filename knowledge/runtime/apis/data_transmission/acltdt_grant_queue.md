---
type: API
title: acltdtGrantQueue
description: "向其他进程授予队列管理、入队或出队权限，可组合权限位；固定来源版本尚无支持产品。"
tags:
- task.lookup
- topic.implementation.cross_process
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
# acltdtGrantQueue

## 功能说明

给其他进程授予队列权限。

## 函数原型

```c
aclError acltdtGrantQueue(uint32_t qid, int32_t pid, uint32_t permission, int32_t timeout)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| qid | 输入 | 队列 ID。 |
| pid | 输入 | 被授权进程 ID。 |
| permission | 输入 | MANAGE/DEQUEUE/ENQUEUE 逻辑或。 |
| timeout | 输入 | 超时时间。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

所有平台均不支持（当前版本无产品落地）。
