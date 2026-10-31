---
type: API
title: aclmdlRITaskDisable
description: "将 RI 中指定任务禁用、不再调度，之后须调用 RIUpdate；同一 RI 不支持并发调用，属于试验特性。"
tags:
- task.lookup
- topic.graph_execution
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
# aclmdlRITaskDisable

> **须知：本接口为试验特性，后续版本可能会存在变更，不支持应用于生产环境中。**

## 功能说明

将指定任务设置为 disable 状态，不再参与调度。试验特性。

## 函数原型

```c
aclError aclmdlRITaskDisable(aclmdlRITask task)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| task | 输入 | 指定任务。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

同一 RI 不支持并发调用。调用后需 Update 更新模型。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`6_scenarios/fault_tolerant_exec/0_model_task_fallback/model_task_fallback.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/6_scenarios/fault_tolerant_exec/0_model_task_fallback/model_task_fallback.cpp#L228)
