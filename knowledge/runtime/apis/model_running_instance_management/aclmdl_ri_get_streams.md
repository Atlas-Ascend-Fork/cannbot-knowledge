---
type: API
title: aclmdlRIGetStreams
description: "枚举模型运行实例关联的 Stream；先传 NULL 查询数量，再提供数组获取列表，属于试验特性。"
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/15_model_running_instance_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/model_ri.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- a3
- a2
---
# aclmdlRIGetStreams

> **须知：本接口为试验特性，后续版本可能会存在变更，不支持应用于生产环境中。**

## 功能说明

获取模型运行实例关联的 Stream。支持两次调用模式。试验特性。

## 函数原型

```c
aclError aclmdlRIGetStreams(aclmdlRI modelRI, aclrtStream *streams, uint32_t *numStreams)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| modelRI | 输入 | 模型运行实例。 |
| streams | 输入&输出 | 传入 NULL 获取数量；传入数组获取列表。 |
| numStreams | 输入&输出 | 输入数组大小，输出实际数量。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

试验特性，不支持应用于生产环境。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/5_reusable_buffer_reset/reusable_buffer_reset.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/5_reusable_buffer_reset/reusable_buffer_reset.cpp#L99)
- [`6_scenarios/fault_tolerant_exec/0_model_task_fallback/model_task_fallback.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/fault_tolerant_exec/0_model_task_fallback/model_task_fallback.cpp#L159)
