---
type: API
title: aclmdlRIDestroy
description: "在模型任务执行完成后销毁运行实例并释放资源，不用于中止仍在运行的任务。"
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.resource_lifecycle
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
- '310b'
- '310p'
- '910'
---
# aclmdlRIDestroy

## 功能说明

销毁模型运行实例。

## 函数原型

```c
aclError aclmdlRIDestroy(aclmdlRI modelRI)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| modelRI | 输入 | 模型运行实例。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

任务执行完毕后调用以释放资源。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/label/0_simple_label/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/label/0_simple_label/main.cpp#L130)
- [`2_advanced_features/model_ri/0_simple_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/0_simple_model/main.cpp#L111)
- [`2_advanced_features/model_ri/1_model_update/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/1_model_update/main.cpp#L125)
