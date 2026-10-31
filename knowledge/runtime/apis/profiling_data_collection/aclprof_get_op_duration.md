---
type: API
title: aclprofGetOpDuration
description: 获取算子执行的耗时时间（单位 us）。
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-03_subscription_to_operator_information.md
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

# aclprofGetOpDuration

## 功能说明

获取指定算子执行的耗时时间，单位微秒。

## 函数原型

```c
uint64_t aclprofGetOpDuration(const void *opInfo, size_t opInfoLen, uint32_t index)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| opInfo | 输入 | 包含算子信息的地址 |
| opInfoLen | 输入 | 算子信息长度 |
| index | 输入 | 算子索引 |

## 返回值说明

返回算子执行耗时（微秒）。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/2_subscribe_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/2_subscribe_model/main.cpp#L49)
