---
type: API
title: aclprofRangeStop
description: "按 RangeStart 返回的 rangeId 结束 msproftx 时间区间，支持在另一线程完成结束记录。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclprofRangeStop

## 功能说明

msproftx 记录事件时间跨度的结束时间。与 [aclprofRangeStart](aclprof_range_start.md) 配对使用，支持跨线程。

## 函数原型

```c
aclError aclprofRangeStop(uint32_t rangeId)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| rangeId | 输入 | [aclprofRangeStart](aclprof_range_start.md) 返回的唯一标识 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofRangeStart](aclprof_range_start.md) 成对使用。
- 支持跨线程调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L110)
