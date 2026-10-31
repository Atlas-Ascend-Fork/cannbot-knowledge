---
type: API
title: aclrtCreateGroupInfo
description: "申请保存 Group 信息的结构体，供 GetAllGroupInfo 填写；不支持 Group 或没有 Group 时返回空指针，使用后需 DestroyGroupInfo。"
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
# aclrtCreateGroupInfo

## 功能说明

创建 aclrtGroupInfo 类型的内存块。

## 函数原型

```c
aclrtGroupInfo *aclrtCreateGroupInfo()
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |

## 返回值说明

返回 aclrtGroupInfo 指针；无 Group 或不支持时返回 nullptr。

## 约束说明

仅 Atlas 推理系列 Control CPU 开放形态。需通过 DestroyGroupInfo 销毁。
