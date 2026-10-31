---
type: API
title: aclrtCreateStreamConfigHandle
description: "创建供 CreateStreamV2 使用的 Stream 配置对象，可通过 SetStreamConfigOpt 填写属性，使用后销毁配置句柄。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_c/runtime/stream.c
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms: []
---

# aclrtCreateStreamConfigHandle

## 功能说明

创建aclrtStreamConfigHandle类型的数据，表示一个Stream的配置对象。
如需销毁aclrtStreamConfigHandle类型的数据，请参见[aclrtDestroyStreamConfigHandle](aclrt_destroy_stream_config_handle.md)。

## 函数原型

```c
aclrtStreamConfigHandle *aclrtCreateStreamConfigHandle(void)
```

## 参数说明

无

## 返回值说明

- 返回aclrtStreamConfigHandle类型的指针，表示成功。
- 返回NULL，表示失败。
