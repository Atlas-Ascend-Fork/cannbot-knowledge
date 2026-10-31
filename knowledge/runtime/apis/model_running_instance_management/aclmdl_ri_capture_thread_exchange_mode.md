---
type: API
title: aclmdlRICaptureThreadExchangeMode
description: 切换当前线程的捕获模式。传入新模式，返回旧模式。
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
# aclmdlRICaptureThreadExchangeMode

## 功能说明

切换当前线程的捕获模式。传入新模式，返回旧模式。

## 函数原型

```c
aclError aclmdlRICaptureThreadExchangeMode(aclmdlRICaptureMode *mode)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| mode | 输入&输出 | 传入新捕获模式，返回之前设置的模式。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

建议在 CaptureBegin 与 CaptureEnd 之间调用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/model_ri/0_simple_model/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/model_ri/0_simple_model/main.cpp#L87)
