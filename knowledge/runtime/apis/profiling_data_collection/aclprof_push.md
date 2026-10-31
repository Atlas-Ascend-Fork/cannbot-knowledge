---
type: API
title: aclprofPush
description: "以 Stamp 开始 msproftx 时间区间，须在同一线程用 Pop 结束；跨线程区间应使用 RangeStart/RangeStop。"
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

# aclprofPush

## 功能说明

msproftx 记录事件时间跨度的开始时间。调用后自动在 Stamp 中记录开始时间戳，Event type 设置为 Push/Pop。

## 函数原型

```c
aclError aclprofPush(void *stamp)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| stamp | 输入 | [aclprofCreateStamp](aclprof_create_stamp.md) 创建的 Stamp 指针 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofPop](aclprof_pop.md) 成对使用。
- 不能跨线程调用（跨线程请用 RangeStart/Stop）。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L104)
