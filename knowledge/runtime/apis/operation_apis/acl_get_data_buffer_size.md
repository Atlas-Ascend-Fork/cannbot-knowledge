---
type: API
title: aclGetDataBufferSize
description: "以 uint32 返回 DataBuffer 记录的字节数；后续版本将废弃，推荐使用返回 size_t 的 aclGetDataBufferSizeV2。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
- topic.implementation.api_layer.c_api
- topic.quality.compatibility.deprecation
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_base_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/data_buffer.cpp
  role: implementation
source_headers:
- include/external/acl/acl_base_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclGetDataBufferSize

## 功能说明

**须知：此接口后续版本会废弃，请使用[aclGetDataBufferSizeV2](acl_get_data_buffer_size_v2.md)接口。**
获取aclDataBuffer类型中数据的内存大小，单位Byte。

## 函数原型

```c
uint32 aclGetDataBufferSize(const aclDataBuffer *dataBuffer)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataBuffer | 输入 | aclDataBuffer类型的指针。<br>需提前调用[aclCreateDataBuffer](acl_create_data_buffer.md)接口创建aclDataBuffer类型的数据。 |

## 返回值说明

aclDataBuffer类型中数据的内存大小。
