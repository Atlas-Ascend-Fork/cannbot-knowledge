---
type: API
title: aclrtDestroyStreamConfigHandle
description: "释放 CreateStreamConfigHandle 创建的 Stream 配置对象；操作对象是创建流所用的配置句柄。"
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

# aclrtDestroyStreamConfigHandle

## 功能说明

销毁通过[aclrtCreateStreamConfigHandle](aclrt_create_stream_config_handle.md)接口创建的aclrtStreamConfigHandle类型的数据。

## 函数原型

```c
aclError aclrtDestroyStreamConfigHandle(aclrtStreamConfigHandle *handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| handle | 输入 | 待销毁的aclrtStreamConfigHandle类型的指针。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
