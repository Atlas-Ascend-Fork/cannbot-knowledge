---
type: API
title: aclAppLog
description: 将日志记录到日志文件中，提供 ACL_APP_LOG 宏封装。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_base_rt.h
  role: header
source_headers:
- include/external/acl/acl_base_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclAppLog

## 功能说明

将日志记录到日志文件中。提供 ACL_APP_LOG 宏，自动填充函数名、文件名和行号。

内部行为（固定 commit 源码结论）：实现中先检查 fmt/func/file 不为 NULL，再检查日志级别是否启用，然后格式化字符串。使用 `vsnprintf_truncated_s` 而非 `vsnprintf_s` 以截断超长内容而非丢弃。超长时最终日志尾部追加 `...[truncated]` 标记。

## 函数原型

```c
void aclAppLog(aclLogLevel logLevel, const char *func, const char *file, uint32_t line, const char *fmt, ...)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| logLevel | 输入 | 日志级别（ACL_DEBUG/INFO/WARNING/ERROR） |
| func | 输入 | 固定 __FUNCTION__ |
| file | 输入 | 固定 __FILE__ |
| line | 输入 | 固定 __LINE__ |
| fmt | 输入 | 日志描述 |

## 返回值说明

无。