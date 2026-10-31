---
type: API
title: aclprofGetOpAttriValue
description: "从 opInfo 中按算子索引读取订阅属性，当前支持线程 ID；返回属性字符串，失败返回 NULL。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/19-03_subscription_to_operator_information.md
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

# aclprofGetOpAttriValue

## 功能说明

获取指定算子的属性值。当前支持获取线程 ID（ACL_SUBSCRIBE_ATTRI_THREADID）。

## 函数原型

```c
const char *aclprofGetOpAttriValue(const void *opInfo, size_t opInfoLen, uint32_t index, aclprofSubscribeOpAttri attri)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| opInfo | 输入 | 包含算子信息的地址 |
| opInfoLen | 输入 | 算子信息长度 |
| index | 输入 | 算子索引 |
| attri | 输入 | 属性类型，如 ACL_SUBSCRIBE_ATTRI_THREADID |

## 返回值说明

返回属性值字符串指针。返回 NULL 表示获取失败。