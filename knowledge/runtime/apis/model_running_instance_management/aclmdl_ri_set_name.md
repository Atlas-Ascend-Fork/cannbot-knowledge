---
type: API
title: aclmdlRISetName
description: 设置模型运行实例的名称。
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
- '310b'
- '310p'
- '910'
---
# aclmdlRISetName

## 功能说明

设置模型运行实例的名称。

## 函数原型

```c
aclError aclmdlRISetName(aclmdlRI modelRI, const char *name)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| modelRI | 输入 | 模型运行实例。 |
| name | 输入 | 名称字符串。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

多次设置以最后一次为准。
