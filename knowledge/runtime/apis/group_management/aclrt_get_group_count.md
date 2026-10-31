---
type: API
title: aclrtGetGroupCount
description: 查询当前 Context 下可用的 Group 个数。
tags:
- task.lookup
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/16_group_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/group.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '310p'
---
# aclrtGetGroupCount

## 功能说明

查询当前 Context 下可用的 Group 个数。

## 函数原型

```c
aclError aclrtGetGroupCount(uint32_t *count)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| count | 输出 | 可用 Group 个数。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

仅 Atlas 推理系列 Control CPU 开放形态。
