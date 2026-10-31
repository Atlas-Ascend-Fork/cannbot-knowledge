---
type: API
title: aclrtGetMemUsageInfo
description: 查询组件的内存使用信息，包括组件名称、当前和峰值内存大小。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-01_device_memory_malloc_and_free.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtGetMemUsageInfo

## 功能说明

查询组件的内存使用信息，包括组件名称、当前和峰值内存大小。

## 函数原型

```c
aclError aclrtGetMemUsageInfo(int32_t deviceId, aclrtMemUsageInfo *memUsageInfo, size_t inputNum, size_t *outputNum)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| deviceId | 输入 | Device ID，取值范围 [0, 可用 Device 数-1) |
| memUsageInfo | 输入&输出 | aclrtMemUsageInfo 结构体数组，按当前内存占用量从大到小排序 |
| inputNum | 输入 | 需查询的组件数量 |
| outputNum | 输出 | 实际查询到的组件数量 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
