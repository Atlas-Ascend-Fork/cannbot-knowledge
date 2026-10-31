---
type: API
title: aclmdlRICaptureTaskUpdateBegin
description: "对已有任务组开始更新，Stream 此时必须不在捕获状态；更新任务的数量、类型须与原组一致，并与 UpdateEnd 配对。"
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
- '310p'
---
# aclmdlRICaptureTaskUpdateBegin

## 功能说明

标记待更新任务的开始。

## 函数原型

```c
aclError aclmdlRICaptureTaskUpdateBegin(aclrtStream stream, aclrtTaskGrp handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream，必须不在捕获状态。 |
| handle | 输入 | 任务组句柄。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

与 CaptureTaskUpdateEnd 成对使用。任务数量、类型须与 TaskGrpBegin/End 一致。部分平台需驱动 >=25.0.RC1 或 26.0.RC1。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/1_model_update/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/1_model_update/main.cpp#L111)
