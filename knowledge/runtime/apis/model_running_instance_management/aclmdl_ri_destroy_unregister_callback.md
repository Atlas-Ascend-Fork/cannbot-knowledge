---
type: API
title: aclmdlRIDestroyUnregisterCallback
description: "按 RI 和函数指针取消销毁回调，取消后该 RI 销毁时不再调用该函数；试验特性。"
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.callback
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
# aclmdlRIDestroyUnregisterCallback

> **须知：本接口为试验特性，后续版本可能会存在变更，不支持应用于生产环境中。**

## 功能说明

取消注册的回调函数。试验特性。

## 函数原型

```c
aclError aclmdlRIDestroyUnregisterCallback(aclmdlRI modelRI, aclrtCallback func)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| modelRI | 输入 | 模型运行实例。 |
| func | 输入 | 回调函数。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

取消注册后销毁 RI 时不再调用该回调。
