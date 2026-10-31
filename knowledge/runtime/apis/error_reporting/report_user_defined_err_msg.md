---
type: API
title: ReportUserDefinedErrMsg
description: 开发者上报自定义错误码，推荐使用 U 码段（如 EU0001）。
tags:
- task.lookup
- task.debugging
- topic.implementation.error_handling
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/22_error_reporting_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/dfx/base/err_msg.h
  role: header
source_headers:
- include/dfx/base/err_msg.h
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

# ReportUserDefinedErrMsg

## 功能说明

开发者上报自定义错误码。推荐使用 U 码段（如 EU0001）。非 6 位字符、以 8888 或 9999 结尾等不推荐形式内部会以 EU0000 上报。

格式化字符串长度（含 \0）超过 1024 时返回 -1。

## 函数原型

```c
int32_t ReportUserDefinedErrMsg(const char *error_code, const char *format, ...)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| error_code | 输入 | 用户自定义错误码 |
| format | 输入 | 错误码对应的错误信息 |
| ... | 输入 | format 中占位符对应的变量值 |

## 返回值

- 0：成功。
- -1：失败。