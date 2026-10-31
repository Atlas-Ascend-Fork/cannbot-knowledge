---
type: API
title: acldumpUnregCallback
description: 取消注册 Dump 数据回调函数，与 acldumpRegCallback 配对使用。
tags:
- task.lookup
- task.debugging
- topic.implementation.debugging
- topic.implementation.callback
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/18_dump_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_dump.h
  role: header
source_headers:
- include/external/acl/acl_dump.h
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

# acldumpUnregCallback

## 功能说明

取消 Dump 数据回调函数注册。取消后 Dump 数据恢复原有落盘行为。

## 函数原型

```c
void acldumpUnregCallback()
```

## 参数说明

无

## 返回值说明

无

## 约束说明

- 必须在 [acldumpRegCallback](acldump_reg_callback.md) 之后调用才有效。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/adump/1_adump_callback/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/adump/1_adump_callback/main.cpp#L178)
