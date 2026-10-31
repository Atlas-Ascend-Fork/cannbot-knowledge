---
type: API
title: aclprofSetConfig
description: "在 Profiling Start 前配置额外采集参数，扩展 CreateConfig 的配置项；支持多次调用，配置字符串最长 256 字节。"
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

# aclprofSetConfig

## 功能说明

[aclprofCreateConfig](../operation_apis/aclprof_create_config.md) 的扩展接口，用于配置额外的性能数据采集参数。支持多次调用。

## 函数原型

```c
aclError aclprofSetConfig(aclprofConfigType configType, const char *config, size_t configLength)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| configType | 输入 | 性能数据采集参数类型，参见 aclprofConfigType |
| config | 输入 | 配置项参数值 |
| configLength | 输入 | config 长度，最大 256 字节 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 需在 [aclprofStart](aclprof_start.md) 之前调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/0_create_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/0_create_config/main.cpp#L41)
- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L152)
