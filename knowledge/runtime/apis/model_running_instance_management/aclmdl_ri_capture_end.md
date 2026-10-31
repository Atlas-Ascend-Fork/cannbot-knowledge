---
type: API
title: aclmdlRICaptureEnd
description: "结束 Stream 捕获并返回保存任务的 RI，须与 CaptureBegin 使用同一 Stream；非 RELAXED 模式还须同线程。"
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
# aclmdlRICaptureEnd

## 功能说明

结束 Stream 的捕获动作，获取暂存任务的模型运行实例。

## 函数原型

```c
aclError aclmdlRICaptureEnd(aclrtStream stream, aclmdlRI *modelRI)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。需与 CaptureBegin 的 Stream 相同。 |
| modelRI | 输出 | 暂存所捕获任务的模型运行实例。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

与 [aclmdlRICaptureBegin](aclmdl_ri_capture_begin.md) 成对使用。若 mode 非 RELAXED，需在同一线程。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/0_simple_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/0_simple_model/main.cpp#L96)
- [`2_advanced_features/model_ri/1_model_update/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/1_model_update/main.cpp#L102)
- [`2_advanced_features/model_ri/3_cond_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/3_cond_model/main.cpp#L89)
