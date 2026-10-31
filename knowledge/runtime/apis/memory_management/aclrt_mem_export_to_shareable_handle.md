---
type: API
title: aclrtMemExportToShareableHandle
description: "将物理内存 handle 导出为 AI Server 内跨进程共享的整数句柄，可启用 PID 白名单；跨 Device 需先开启 PeerAccess。"
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
# aclrtMemExportToShareableHandle

## 功能说明

导出物理内存 handle 供其他进程共享。

## 函数原型

```c
aclError aclrtMemExportToShareableHandle(aclrtDrvMemHandle handle, aclrtMemHandleType handleType, uint64_t flags, uint64_t *shareableHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | 物理内存信息 handle |
| handleType | 输入 | 预留参数，固定 ACL_MEM_HANDLE_TYPE_NONE |
| flags | 输入 | 是否启用进程白名单校验（DEFAULT / DISABLE_PID_VALIDATION） |
| shareableHandle | 输出 | 标识共享给其他进程的 shareableHandle |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- handle 与 shareableHandle 一一对应
- 支持 AI Server 内跨进程共享，跨 Device 需配合 aclrtDeviceEnablePeerAccess

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp#L76)
- [`1_basic_features/memory/8_physical_memory_sharing_withoutpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/8_physical_memory_sharing_withoutpid/proc_a.cpp#L76)
