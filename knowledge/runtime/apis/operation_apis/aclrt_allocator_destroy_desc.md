---
type: API
title: aclrtAllocatorDestroyDesc
description: 销毁通过aclrtAllocatorCreateDesc接口创建的aclrtAllocatorDesc类型的数据。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/allocator.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclrtAllocatorDestroyDesc

## 功能说明

销毁通过[aclrtAllocatorCreateDesc](aclrt_allocator_create_desc.md)接口创建的aclrtAllocatorDesc类型的数据。

## 函数原型

```c
aclError aclrtAllocatorDestroyDesc(aclrtAllocatorDesc allocatorDesc)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| allocatorDesc | 输入 | 待销毁的aclrtAllocatorDesc类型的数据。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/allocator/0_custom_allocator/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/allocator/0_custom_allocator/main.cpp#L128)
