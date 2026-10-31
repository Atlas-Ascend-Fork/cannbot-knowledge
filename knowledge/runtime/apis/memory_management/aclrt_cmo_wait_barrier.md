---
type: API
title: aclrtCmoWaitBarrier
description: "在已绑定模型的 Stream 上等待指定 barrierId 的 INVALID Cache 操作完成，与带屏障的 CMO 下发配合。"
tags:
- task.lookup
- topic.data_movement.memory_access
- topic.implementation.synchronization
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-06_CMO_memory_operation.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '310b'
---
# aclrtCmoWaitBarrier

## 功能说明

等待具有指定 barrierId 的 Invalid 内存操作任务执行完成。

## 函数原型

```c
aclError aclrtCmoWaitBarrier(aclrtBarrierTaskInfo *taskInfo, aclrtStream stream, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| taskInfo | 输入 | Cache 操作的任务信息 |
| stream | 输入 | 执行等待任务的 Stream，仅支持与模型绑定的 Stream |
| flag | 输入 | 预留，固定配置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
