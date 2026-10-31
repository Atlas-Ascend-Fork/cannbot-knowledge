---
type: API
title: aclUpdateDataBuffer
description: "更新 DataBuffer 描述的地址和大小；旧数据内存仍由用户管理，不再使用时须自行释放。"
tags:
- task.lookup
- topic.memory
- topic.implementation.api_layer.c_api
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

# aclUpdateDataBuffer

## 功能说明

更新aclDataBuffer中数据的内存及大小。
更新aclDataBuffer后，之前aclDataBuffer中存放数据的内存如果不使用，需及时释放，否则可能会导致内存泄漏。

## 函数原型

```c
aclError aclUpdateDataBuffer(aclDataBuffer *dataBuffer, void *data, size_t size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataBuffer | 输入 | aclDataBuffer类型的指针。<br>需提前调用[aclCreateDataBuffer](acl_create_data_buffer.md)接口创建aclDataBuffer类型的数据。<br>该内存需由用户自行管理，调用[aclrtMalloc](../memory_management/aclrt_malloc.md)接口/[aclrtFree](../memory_management/aclrt_free.md)接口申请/释放内存，或调用[aclrtMallocHost](../memory_management/aclrt_malloc_host.md)接口/[aclrtFreeHost](../memory_management/aclrt_free_host.md)接口申请/释放内存。 |
| data | 输入 | 存放数据内存地址的指针。 |
| size | 输入 | 内存大小，单位Byte。<br>如果用户需要使用空tensor，则在申请内存时，内存大小最小为1Byte，以保障后续业务正常运行。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
