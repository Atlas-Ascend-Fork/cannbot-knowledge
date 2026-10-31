---
type: API
title: aclprofCreateStamp
description: "在 Profiling Start 之后创建 msproftx Stamp，供瞬时标记或时间区间打点使用，须与 DestroyStamp 配对。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.resource_lifecycle
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclprofCreateStamp

## 功能说明

创建 msproftx 事件标记（Stamp）。创建的 Stamp 供 [aclprofMark](aclprof_mark.md)、[aclprofSetStampTraceMessage](aclprof_set_stamp_trace_message.md)、[aclprofPush](aclprof_push.md)、[aclprofRangeStart](aclprof_range_start.md) 等接口使用。

## 函数原型

```c
void *aclprofCreateStamp()
```

## 返回值说明

- 返回 void 指针表示成功。
- 返回 nullptr 表示失败。

## 约束说明

- 与 [aclprofDestroyStamp](aclprof_destroy_stamp.md) 配对使用。
- 需在 [aclprofStart](aclprof_start.md) 之后调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L21)
