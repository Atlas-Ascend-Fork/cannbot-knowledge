---
type: API
title: aclprofStop
description: "按与 Start 一致的配置停止本次 Profiling 采集，与 Start 配对；初始化生命周期结束另用 Finalize。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-01_data_profiling_apis.md
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

# aclprofStop

## 功能说明

停止 Profiling 数据采集，与 [aclprofStart](aclprof_start.md) 配对使用。

## 函数原型

```c
aclError aclprofStop(const aclprofConfig *profilerConfig)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| profilerConfig | 输入 | 停止采集的配置，需与 Start 时保持一致 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofStart](aclprof_start.md) 配对使用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/0_create_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/0_create_config/main.cpp#L58)
- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L159)
