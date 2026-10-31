---
type: API
title: aclmdlRIDebugPrint
description: "在 CaptureEnd 之后打印模型运行实例的内部信息，仅供维测使用；需要 JSON 文件时使用 DebugJsonPrint。"
tags:
- task.lookup
- task.debugging
- topic.graph_execution
- topic.implementation.debugging
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
# aclmdlRIDebugPrint

## 功能说明

维测场景下打印内部模型信息。

## 函数原型

```c
aclError aclmdlRIDebugPrint(aclmdlRI modelRI)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| modelRI | 输入 | 模型运行实例。仅支持 CaptureEnd 之后打印。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

仅维测场景使用。
