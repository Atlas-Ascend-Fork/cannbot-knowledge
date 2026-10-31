---
type: API
title: aclprofGetOpFlag
description: "从 opInfo 中识别指定节点属于算子、子图还是算子线程，返回订阅类型标记，失败返回 NONE。"
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

# aclprofGetOpFlag

## 功能说明

获取指定算子的订阅类型标记，返回值指示该节点是算子、子图还是算子 thread。

## 函数原型

```c
aclprofSubscribeOpFlag aclprofGetOpFlag(const void *opInfo, size_t opInfoLen, uint32_t index)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| opInfo | 输入 | 包含算子信息的地址 |
| opInfoLen | 输入 | 算子信息长度 |
| index | 输入 | 算子索引 |

## 返回值说明

返回 aclprofSubscribeOpFlag 枚举：ACL_SUBSCRIBE_OP（算子）、ACL_SUBSCRIBE_SUBGRAPH（子图）、ACL_SUBSCRIBE_OP_THREAD、ACL_SUBSCRIBE_NONE（失败）。