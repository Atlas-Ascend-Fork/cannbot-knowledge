---
type: API
title: aclprofRangePop
description: "上报 RangePushEx 缓存的 Torch Tensor 信息，配对完成该次 Profiling 数据上报。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-02_msproftx_extension_apis.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
source_headers:
- include/external/acl/acl_prof.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclprofRangePop

## 功能说明

在 Torch 场景下，用户在算子加载前先调用 [aclprofRangePushEx](aclprof_range_push_ex.md)，后调用本接口完成 Profiling 数据上报。调用后上报缓存的 Tensor 信息。

## 函数原型

```c
aclError aclprofRangePop()
```

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 与 [aclprofRangePushEx](aclprof_range_push_ex.md) 配对使用。