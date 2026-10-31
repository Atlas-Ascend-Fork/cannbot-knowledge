---
type: API
title: aclprofStr2Id
description: 将字符串转换为哈希 ID，用于 msproftx 标记。
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclprofStr2Id

## 功能说明

msproftx 用于将字符串（如算子名）转化为哈希 ID，作为 Tensor 信息中的标识。

## 函数原型

```c
uint64_t aclprofStr2Id(const char *message)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| message | 输入 | 字符信息，例如算子名 |

## 返回值说明

返回哈希 ID。uint64_t 最大值表示失败。

## 约束说明

- 配合 [aclprofRangePushEx](aclprof_range_push_ex.md)/[aclprofRangePop](aclprof_range_pop.md) 使用，在 RangePushEx 之前调用。