---
type: API
title: aclprofDestroyStamp
description: "释放 msproftx Stamp，与 CreateStamp 配对；须在 aclprofStop 停止采集前调用。"
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

# aclprofDestroyStamp

## 功能说明

释放 msproftx 事件标记（Stamp），与 [aclprofCreateStamp](aclprof_create_stamp.md) 配对使用。

## 函数原型

```c
void aclprofDestroyStamp(void *stamp)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| stamp | 输入 | 待释放的 Stamp 指针 |

## 返回值说明

无

## 约束说明

- 与 [aclprofCreateStamp](aclprof_create_stamp.md) 配对使用。
- 在 [aclprofStop](aclprof_stop.md) 之前调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L31)
