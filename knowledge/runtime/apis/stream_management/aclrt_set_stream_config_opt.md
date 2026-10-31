---
type: API
title: aclrtSetStreamConfigOpt
description: "向 Stream 配置句柄写入属性值及长度，供 aclrtCreateStreamV2 创建流时使用；与运行中 Stream 属性设置区分。"
tags:
- task.lookup
- topic.implementation
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms: []
---

# aclrtSetStreamConfigOpt

## 功能说明

设置 Stream 配置对象中的属性取值，配合 [aclrtCreateStreamConfigHandle](../operation_apis/aclrt_create_stream_config_handle.md) 和 [aclrtCreateStreamV2](aclrt_create_stream_v2.md) 使用。

## 函数原型

```c
aclError aclrtSetStreamConfigOpt(aclrtStreamConfigHandle *handle, aclrtStreamConfigAttr attr, const void *attrValue, size_t valueSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| handle | 输出 | Stream 配置对象指针 |
| attr | 输入 | 属性类型 |
| attrValue | 输入 | 属性值指针 |
| valueSize | 输入 | attrValue 数据长度 |

## 返回值说明

返回 0 表示成功，其他值表示失败。