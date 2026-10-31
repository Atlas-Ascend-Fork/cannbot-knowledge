---
type: API
title: ReportPredefinedErrMsg
description: 上报 CANN 预定义用户类错误信息，支持带参数或无条件两种形式。
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

# ReportPredefinedErrMsg

## 功能说明

上报 CANN 预定义的用户类错误信息。提供封装宏 REPORT_PREDEFINED_ERR_MSG。

支持两种形式：无条件错误码直接传入 error_code；带参数形式传入 key/value 向量替换 error_code.json 中 ErrMessage 的占位符。

## 函数原型

```c
int32_t ReportPredefinedErrMsg(const char *error_code)
int32_t ReportPredefinedErrMsg(const char *error_code, const std::vector<const char *> &key, const std::vector<const char *> &value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| error_code | 输入 | 6 位错误码（如 E10001），0000~8999 为用户类错误 |
| key | 输入 | 预定义参数列表 |
| value | 输入 | 参数实际值，替换 ErrMessage 占位符 |

## 返回值

- 0：成功。
- -1：失败。