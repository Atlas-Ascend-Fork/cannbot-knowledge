---
type: API
title: aclrtCreateStreamV2
description: "按 Stream 配置句柄创建 Stream；先用 CreateStreamConfigHandle 创建配置，再用 SetStreamConfigOpt 设置属性。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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

# aclrtCreateStreamV2

## 功能说明

创建 Stream 并支持附加配置。需配合 [aclrtCreateStreamConfigHandle](../operation_apis/aclrt_create_stream_config_handle.md)、[aclrtSetStreamConfigOpt](aclrt_set_stream_config_opt.md) 一起使用。

## 函数原型

```c
aclError aclrtCreateStreamV2(aclrtStream *stream, const aclrtStreamConfigHandle *handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| stream | 输出 | 创建的 Stream 指针 |
| handle | 输入 | Stream 配置对象 |

## 返回值说明

返回 0 表示成功，其他值表示失败。

## 约束说明

- 需配合 [aclrtCreateStreamConfigHandle](../operation_apis/aclrt_create_stream_config_handle.md)、[aclrtSetStreamConfigOpt](aclrt_set_stream_config_opt.md) 使用。