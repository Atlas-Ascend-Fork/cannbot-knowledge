---
type: API
title: aclrtGetAllGroupInfo
description: "查询当前 Context 下全部 Group 的信息，写入 CreateGroupInfo 申请的结构体，再用 GetGroupInfoDetail 提取属性。"
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
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '310p'
---
# aclrtGetAllGroupInfo

## 功能说明

查询当前 Context 下所有 Group 的算力信息。

## 函数原型

```c
aclError aclrtGetAllGroupInfo(aclrtGroupInfo *groupInfo)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| groupInfo | 输出 | Group 算力信息。需先 CreateGroupInfo 创建。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

仅 Atlas 推理系列 Control CPU 开放形态。
