---
type: API
title: aclDestroyDataBuffer
description: "销毁 aclDataBuffer 描述对象，不释放创建时传入的 data 内存，底层内存须由用户单独释放。"
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

# aclDestroyDataBuffer

## 功能说明

销毁通过[aclCreateDataBuffer](acl_create_data_buffer.md)接口创建的aclDataBuffer类型的数据。
此处仅销毁aclDataBuffer类型的数据，调用[aclCreateDataBuffer](acl_create_data_buffer.md)接口创建aclDataBuffer类型数据时传入的data的内存需由用户自行释放。

## 函数原型

```c
aclError aclDestroyDataBuffer(const aclDataBuffer *dataBuffer)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataBuffer | 输入 | 待销毁的aclDataBuffer类型的指针。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L201)
