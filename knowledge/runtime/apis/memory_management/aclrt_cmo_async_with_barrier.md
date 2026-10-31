---
type: API
title: aclrtCmoAsyncWithBarrier
description: "向已绑定模型的 Stream 异步下发 Cache 操作；INVALID 类型可携带 barrierId，供后续屏障等待。"
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
# aclrtCmoAsyncWithBarrier

## 功能说明

异步执行 Cache 内存操作并携带 barrierId。

## 函数原型

```c
aclError aclrtCmoAsyncWithBarrier(void *src, size_t size, aclrtCmoType cmoType, uint32_t barrierId, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| src | 输入 | 待操作的 Device 内存地址 |
| size | 输入 | 待操作的内存大小 |
| cmoType | 输入 | Cache 操作类型 |
| barrierId | 输入 | 屏障标识，cmoType 为 INVALID 时有效 |
| stream | 输入 | 执行操作任务的 Stream，仅支持与模型绑定的 Stream |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
