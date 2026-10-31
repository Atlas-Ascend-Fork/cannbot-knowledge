---
type: API
title: aclprofStart
description: "按配置使能 Profiling，采集调用之后的数据，须在模型执行前调用；连续 Start 指定重复 Device 会报错。"
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

# aclprofStart

## 功能说明

下发 Profiling 请求，使能数据采集。在模型执行前调用，采集到的数据为该接口之后的数据。

## 函数原型

```c
aclError aclprofStart(const aclprofConfig *profilerConfig)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| profilerConfig | 输入 | Profiling 配置数据，通过 [aclprofCreateConfig](../operation_apis/aclprof_create_config.md) 创建 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofStop](aclprof_stop.md) 配对使用。
- 连续多次 Start 指定重复 Device 会返回报错。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/0_create_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/0_create_config/main.cpp#L48)
- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L153)
