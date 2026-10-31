---
type: API
title: acllogVaList
description: 通过 va_list 记录用户模块产生的日志。
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

# acllogVaList

## 功能说明

通过 va_list 记录用户模块产生的日志，适用于封装日志函数的场景。参数语义与 [acllogRecord](acllog_record.md) 一致。

## 函数原型

```c
void acllogVaList(int32_t moduleId, int32_t level, const char *fmt, va_list list)
```

## 参数说明

| 参数 | 输入/输出 | 说明 |
| --- | --- | --- |
| moduleId | 输入 | 用户模块 ID |
| level | 输入 | 日志级别 |
| fmt | 输入 | 待打印内容 |
| list | 输入 | va_list 可变参数列表 |

## 返回值

无。