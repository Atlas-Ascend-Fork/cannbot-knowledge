---
type: API
title: aclrtCacheLastTaskOpInfo
description: 捕获模式下缓存算子信息到最后下发的任务上。
tags:
- task.lookup
- topic.graph_execution
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
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

# aclrtCacheLastTaskOpInfo

## 功能说明

基于捕获方式构建模型运行实例场景下，将指定内存中的算子信息缓存到当前线程最后下发的任务上。需配合 [aclmdlRICaptureBegin](../model_running_instance_management/aclmdl_ri_capture_begin.md)/End、[aclrtSetStreamAttribute](../stream_management/aclrt_set_stream_attribute.md) 使用。

## 函数原型

```c
aclError aclrtCacheLastTaskOpInfo(const void * const infoPtr, const size_t infoSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| infoPtr | 输入 | Host 内存中的缓存信息地址 |
| infoSize | 输入 | 内存大小，(0, 64K] |

## 返回值说明

返回 0 表示成功，其他值表示失败。