---
type: API
title: aclrtMemImportFromShareableHandle
description: "将整数共享句柄导入到指定 Device，返回当前进程的物理内存 handle；共享内存须仍存在，不支持同进程导出再导入。"
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
# aclrtMemImportFromShareableHandle

## 功能说明

导入共享内存句柄，返回本进程中的物理内存 handle。

## 函数原型

```c
aclError aclrtMemImportFromShareableHandle(uint64_t shareableHandle, int32_t deviceId, aclrtDrvMemHandle *handle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| shareableHandle | 输入 | 待共享的 shareableHandle |
| deviceId | 输入 | 生成指定 Device 上的 handle |
| handle | 输出 | 本进程的物理内存 handle |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 调用前需保证待共享的物理内存存在
- 不支持同进程同时调用 export 和 import

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/7_physical_memory_sharing_withpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/7_physical_memory_sharing_withpid/proc_b.cpp#L45)
- [`1_basic_features/memory/8_physical_memory_sharing_withoutpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/8_physical_memory_sharing_withoutpid/proc_b.cpp#L35)
