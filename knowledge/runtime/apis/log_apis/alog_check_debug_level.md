---
type: API
title: AlogCheckDebugLevel
description: 校验调测日志级别（该接口后续版本将废弃）。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
- topic.quality.compatibility.deprecation
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/23_log_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/dfx/base/alog_pub.h
  role: header
source_headers:
- include/dfx/base/alog_pub.h
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

# AlogCheckDebugLevel

## 功能说明

校验调测日志级别。该接口将在后续版本中废弃。

## 函数原型

```c
int32_t AlogCheckDebugLevel(uint32_t moduleId, int32_t level)
```

## 参数说明

| 参数 | 输入/输出 | 说明 |
| --- | --- | --- |
| moduleId | 输入 | 模块 ID |
| level | 输入 | 日志级别 |

## 返回值

1：级别校验通过；0：不通过。