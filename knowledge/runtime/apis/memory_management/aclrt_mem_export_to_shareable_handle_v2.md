---
type: API
title: aclrtMemExportToShareableHandleV2
description: "按 shareType 导出物理内存共享句柄，可选择 AI Server 内或跨 Server 共享；跨 Server 仅 A3 支持。"
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
# aclrtMemExportToShareableHandleV2

## 功能说明

导出物理内存 handle，支持指定共享句柄类型（AI Server 内或跨 Server）。

## 函数原型

```c
aclError aclrtMemExportToShareableHandleV2(aclrtDrvMemHandle handle, uint64_t flags, aclrtMemSharedHandleType shareType, void *shareableHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | 物理内存信息 handle |
| flags | 输入 | 是否启用进程白名单校验 |
| shareType | 输入 | 共享句柄类型，见 aclrtMemSharedHandleType |
| shareableHandle | 输出 | 指向共享句柄的指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅 A3 支持跨 AI Server 共享

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp#L87)
