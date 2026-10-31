---
type: API
title: aclprofSetStampTraceMessage
description: 为 msproftx 事件标记携带字符串描述。
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-02_msproftx_extension_apis.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
source_headers:
- include/external/acl/acl_prof.h
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

# aclprofSetStampTraceMessage

## 功能说明

为 msproftx 事件标记携带字符串描述信息，在 Profiling 解析结果中 msprof_tx summary 数据展示。

## 函数原型

```c
aclError aclprofSetStampTraceMessage(void *stamp, const char *msg, uint32_t msgLen)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| stamp | 输入 | [aclprofCreateStamp](aclprof_create_stamp.md) 创建的 Stamp 指针 |
| msg | 输入 | Stamp 信息字符串指针 |
| msgLen | 输入 | 字符串长度 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 在 CreateStamp 和 DestroyStamp 之间调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L27)
