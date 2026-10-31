---
type: API
title: acllogCheckDebugLevel
description: 校验用户模块调测日志级别。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.resource_query
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

# acllogCheckDebugLevel

## 功能说明

校验用户模块调测日志级别，用户 moduleId 范围为 0xff00~0xffff。

## 函数原型

```c
int32_t acllogCheckDebugLevel(int32_t moduleId, int32_t logLevel)
```

## 参数说明

| 参数 | 输入/输出 | 说明 |
| --- | --- | --- |
| moduleId | 输入 | 用户模块 ID |
| logLevel | 输入 | 日志级别 |

## 返回值

1：通过；0：不通过。