---
type: API
title: aclrtMemSetPidToShareableHandleV2
description: "为 V2 导出的物理内存共享句柄设置 PID 白名单，并显式指定 shareType，与 IPC 字符串 key 的白名单接口区分。"
tags:
- task.lookup
- topic.implementation.cross_process
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
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMemSetPidToShareableHandleV2

## 功能说明

增强版设置共享内存白名单，支持指定共享句柄类型。

## 函数原型

```c
aclError aclrtMemSetPidToShareableHandleV2(void *shareableHandle, aclrtMemSharedHandleType shareType, int32_t *pid, size_t pidNum)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| shareableHandle | 输入 | [aclrtMemExportToShareableHandleV2](aclrt_mem_export_to_shareable_handle_v2.md) 导出的 handle |
| shareType | 输入 | 共享句柄类型 |
| pid | 输入 | 白名单进程 ID 数组 |
| pidNum | 输入 | 白名单进程数量 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。
