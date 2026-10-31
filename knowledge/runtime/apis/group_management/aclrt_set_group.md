---
type: API
title: aclrtSetGroup
description: "为当前运算选择已创建的 Group；先经 DCMI 创建分组，再从 GroupInfo 取得 groupId，仅适用于 Atlas 推理产品 Control CPU 开放场景。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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
# aclrtSetGroup

## 功能说明

指定当前运算使用的 Group。

## 函数原型

```c
aclError aclrtSetGroup(int32_t groupId)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| groupId | 输入 | Group ID。需通过 GetGroupInfoDetail 获取。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

仅 Atlas 推理系列 Control CPU 开放形态。需先通过 DCMI 创建分组。
