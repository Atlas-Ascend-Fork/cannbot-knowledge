---
type: API
title: aclmdlRIEndTask
description: "在 BuildBegin 与 BuildEnd 之间，标记 RI 绑定 Stream 的任务下发结束，供显式模型构建使用。"
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
- '310b'
- '310p'
- '910'
---
# aclmdlRIEndTask

## 功能说明

在 Stream 上标记下发任务结束。

## 函数原型

```c
aclError aclmdlRIEndTask(aclmdlRI modelRI, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| modelRI | 输入 | 模型运行实例。 |
| stream | 输入 | 指定 Stream。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

在 BuildBegin 与 BuildEnd 之间调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/label/0_simple_label/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/label/0_simple_label/main.cpp#L113)
- [`2_advanced_features/model_ri/2_model_switch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/2_model_switch/main.cpp#L162)
- [`3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/cache_maintenance/0_prefetch_strategy_comparison/prefetch_strategy_comparison.cpp#L128)
