---
type: API
title: aclrtMemMapSetLink
description: "为已导入的物理内存 handle 设置映射访问链路；调用顺序为 ImportFromShareableHandle、SetLink、MapMem。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-04_virtual_memory_management.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- a3
---
# aclrtMemMapSetLink

## 功能说明

设置物理内存 handle 在映射时使用的访问链路类型。

## 函数原型

```c
aclError aclrtMemMapSetLink(aclrtDrvMemHandle handle, aclrtMemLinkType adviceLink)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | 物理内存信息 handle（需通过 [aclrtMemImportFromShareableHandle](aclrt_mem_import_from_shareable_handle.md) 获取） |
| adviceLink | 输入 | 内存访问链路类型 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 需先 import 再 set link 最后 map
