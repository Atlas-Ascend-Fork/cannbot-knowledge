---
type: API
title: aclrtGetGroupInfoDetail
description: "从已查询的 Group 信息中按 groupIndex 与属性类型提取具体值；调用方提供输出缓冲区，接口返回实际属性长度。"
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
# aclrtGetGroupInfoDetail

## 功能说明

查询指定 Group 的算力信息。

## 函数原型

```c
aclError aclrtGetGroupInfoDetail(const aclrtGroupInfo *groupInfo, int32_t groupIndex, aclrtGroupAttr attr, void *attrValue, size_t valueLen, size_t *paramRetSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| groupInfo | 输入 | 算力信息。需通过 GetAllGroupInfo 获取。 |
| groupIndex | 输入 | Group 索引 [0, Group 数量)。 |
| attr | 输入 | 算力属性。 |
| attrValue | 输出 | 属性值。 |
| valueLen | 输入 | attrValue 最大长度（Byte）。 |
| paramRetSize | 输出 | 实际返回大小（Byte）。 |

## 返回值说明

返回 0 表示成功，其他值表示失败，请参见 aclError。

## 约束说明

仅 Atlas 推理系列 Control CPU 开放形态。
