---
type: API
title: RegisterFormatErrorMessage
description: 按 JSON 格式注册预定义错误码信息，供 ReportPredefinedErrMsg 使用。
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

# RegisterFormatErrorMessage

## 功能说明

按照 JSON 格式注册预定义错误码信息，注册后再调用 [ReportPredefinedErrMsg](report_predefined_err_msg.md) 上报。提供封装宏 REG_FORMAT_ERROR_MSG，定义静态变量在进程加载时完成注册。

## 函数原型

```c
int32_t RegisterFormatErrorMessage(const char *error_msg, size_t error_msg_len)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| error_msg | 输入 | JSON 格式错误码信息，可一次注册多个 |
| error_msg_len | 输入 | error_msg 长度，不含 \0 |

## 返回值

- 0：成功。
- -1：失败。