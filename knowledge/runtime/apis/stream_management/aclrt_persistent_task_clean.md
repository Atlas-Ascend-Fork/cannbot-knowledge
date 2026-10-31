---
type: API
title: aclrtPersistentTaskClean
description: "清理 ACL_STREAM_PERSISTENT 流中的任务并保留 Stream，供后续重新下发任务，不用于普通流。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/06_stream_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/stream.cpp
  role: implementation
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/runtime/api/api_c_stream.cc
  role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtPersistentTaskClean

## 功能说明

清理 ACL_STREAM_PERSISTENT 类型的 Stream 上的任务，适用于不删除该类型 Stream 的情况下重新下发任务的场景。

内部行为 （固定 commit `b523035a` 源码结论）：

- 委托 `rtsPersistentTaskClean(stream)` 到 RTS 层。

## 函数原型

```c
aclError aclrtPersistentTaskClean(aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 仅 950、A3、A2 支持。
- 仅清理 ACL_STREAM_PERSISTENT 类型的 Stream。
- IPV350 不支持。
