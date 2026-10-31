---
type: API
title: aclCreateDataBuffer
description: "将已有内存地址和大小封装为 aclDataBuffer 描述对象，底层 Host/Device 内存由用户自行申请、释放；空描述要求 data=NULL 且 size=0。"
tags:
- task.lookup
- topic.implementation.resource_lifecycle
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

# aclCreateDataBuffer

## 功能说明

创建aclDataBuffer类型的数据，该数据类型用于描述内存地址、大小等内存信息。
如需销毁aclDataBuffer类型的数据，请参见[aclDestroyDataBuffer](acl_destroy_data_buffer.md)。

## 函数原型

```c
aclDataBuffer *aclCreateDataBuffer(void *data, size_t size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| data | 输入 | 存放数据内存地址的指针。data参数支持传入nullptr，表示创建一个空的数据类型，此时size参数值必须设置为0。<br>该内存需由用户自行管理，调用[aclrtMalloc](../memory_management/aclrt_malloc.md)接口/[aclrtFree](../memory_management/aclrt_free.md)接口申请/释放内存，或调用[aclrtMallocHost](../memory_management/aclrt_malloc_host.md)接口/[aclrtFreeHost](../memory_management/aclrt_free_host.md)接口申请/释放内存。 |
| size | 输入 | 内存大小，单位Byte。<br>如果用户需要使用空tensor，则在申请内存时，内存大小最小为1Byte，以保障后续业务正常运行。 |

## 返回值说明

返回aclDataBuffer类型的指针。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L148)
