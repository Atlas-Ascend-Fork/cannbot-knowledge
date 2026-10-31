---
type: API
title: aclprofGetStepTimestamp
description: "在单算子模型训练中标记迭代开始或结束，将 StepInfo、START/END 标记与 Stream 关联，供 Profiling 解析迭代。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-04_setting_Iteration_time_in_pytorch_scenarios.md
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

# aclprofGetStepTimestamp

## 功能说明

利用单算子模型执行接口实现训练的场景下，标记迭代开始与结束时间，为 Profiling 解析提供迭代标识。

## 函数原型

```c
aclError aclprofGetStepTimestamp(aclprofStepInfo* stepInfo, aclprofStepTag tag, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| stepinfo | 输入 | 迭代信息，通过 [aclprofCreateStepInfo](../operation_apis/aclprof_create_step_info.md) 创建 |
| tag | 输入 | ACL_STEP_START（开始）或 ACL_STEP_END（结束） |
| stream | 输入 | 指定 Stream |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L95)
