---
type: API
title: aclrtDestroyGroupInfo
description: 销毁 aclrtGroupInfo 类型的数据。
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '310p'
---
# aclrtDestroyGroupInfo

## 功能说明

销毁 aclrtGroupInfo 类型的数据。

## 函数原型

```c
aclError aclrtDestroyGroupInfo(aclrtGroupInfo *groupInfo)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| groupInfo | 输入 | 待销毁的 aclrtGroupInfo 指针。 |

## 返回值说明

返回 0 表示成功，非零表示失败。

## 约束说明

仅 Atlas 推理系列 Control CPU 开放形态。只能销毁 CreateGroupInfo 创建的数据。
