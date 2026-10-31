---
type: API
title: aclGetDataBufferAddr
description: 获取aclDataBuffer类型中的数据的内存地址。
tags:
- task.lookup
- topic.implementation.resource_query
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
updated_at: '2026-10-30T07:10:24Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclGetDataBufferAddr

## 功能说明

获取aclDataBuffer类型中的数据的内存地址。

## 函数原型

```c
void *aclGetDataBufferAddr(const aclDataBuffer *dataBuffer)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| dataBuffer | 输入 | aclDataBuffer类型的指针。<br>需提前调用[aclCreateDataBuffer](acl_create_data_buffer.md)接口创建aclDataBuffer类型的数据。 |

## 返回值说明

返回aclDataBuffer类型中的数据的内存地址。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L153)
