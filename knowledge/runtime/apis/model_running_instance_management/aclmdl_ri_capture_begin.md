---
type: API
title: aclmdlRICaptureBegin
description: 开始捕获 Stream 上下发的任务。在 CaptureBegin 与 CaptureEnd 之间下发的任务暂存于内部 RI，不立即执行。
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- a3
- a2
- '310p'
---
# aclmdlRICaptureBegin

## 功能说明

开始捕获 Stream 上下发的任务。在 CaptureBegin 与 CaptureEnd 之间下发的任务暂存于内部 RI，不立即执行。

## 函数原型

```c
aclError aclmdlRICaptureBegin(aclrtStream stream, aclmdlRICaptureMode mode)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| stream | 输入 | 指定 Stream。需提前创建。 |
| mode | 输入 | 捕获模式，限制非安全函数的作用范围。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

需与 [aclmdlRICaptureEnd](aclmdl_ri_capture_end.md) 成对使用，两个接口的 Stream 应相同。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/0_simple_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/0_simple_model/main.cpp#L82)
- [`2_advanced_features/model_ri/1_model_update/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/1_model_update/main.cpp#L90)
- [`2_advanced_features/model_ri/3_cond_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/3_cond_model/main.cpp#L69)
