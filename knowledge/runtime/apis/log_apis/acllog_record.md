---
type: API
title: acllogRecord
description: 记录用户模块产生的日志，moduleId 范围为 0xff00~0xffff。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/23_log_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/dfx/base/acl_log.h
  role: header
source_headers:
- include/dfx/base/acl_log.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# acllogRecord

## 功能说明

用于记录用户模块产生的日志。用户 moduleId 范围为 0xff00~0xffff。如需记录运行日志可传入 moduleId | RUN_LOG_MASK。单条日志最大 1024 字节。

## 函数原型

```c
void acllogRecord(int32_t moduleId, int32_t level, const char *fmt, ...)
```

## 参数说明

| 参数 | 输入/输出 | 说明 |
| --- | --- | --- |
| moduleId | 输入 | 用户模块 ID，0xff00~0xffff，可或 RUN_LOG_MASK |
| level | 输入 | 日志级别 |
| fmt | 输入 | 待打印内容，单条最大 1024 字节 |

## 返回值

无。