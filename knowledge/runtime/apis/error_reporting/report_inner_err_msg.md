---
type: API
title: ReportInnerErrMsg
description: 上报 CANN 预定义内部错误信息，附带文件名、函数名和行号。
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

# ReportInnerErrMsg

## 功能说明

上报 CANN 预定义内部错误信息，同时上报调用处文件名、函数名以及行号。提供封装宏 REPORT_INNER_ERR_MSG。

格式化字符串长度（含 \0）超过 1024 时返回 -1。

## 函数原型

```c
int32_t ReportInnerErrMsg(const char_t *file_name, const char_t *func, uint32_t line, const char *error_code, const char_t *format, ...)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| file_name | 输入 | 文件名，固定配置为 __FILE__ |
| func | 输入 | 函数名，固定配置为 __FUNCTION__ |
| line | 输入 | 行号，固定配置为 __LINE__ |
| error_code | 输入 | 6 位错误码（如 E19999），第 1 位表示级别（E/W/I），9000~9999 为内部错误 |
| format | 输入 | 错误信息 format 字符串 |
| ... | 输入 | 可变参数 |

## 返回值

- 0：成功。
- -1：失败。