---
type: API
title: aclrtIpcMemClose
description: "按 key 关闭 IPC 共享内存；所有导入进程先完成 Close 后，导出进程才能关闭。"
tags:
- task.lookup
- topic.implementation.cross_process
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-07_IPC_memory_sharing.md
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
- a2
- '310p'
- '910'
---
# aclrtIpcMemClose

## 功能说明

关闭 IPC 共享内存。

## 函数原型

```c
aclError aclrtIpcMemClose(const char *key)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| key | 输入 | 通过 [aclrtIpcMemGetExportKey](aclrt_ipc_mem_get_export_key.md) 获取的共享内存 key |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 需确保所有 import 方都 close 后，export 方才可 close

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/10_ipc_memory_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/10_ipc_memory_withpid/proc_a.cpp#L67)
- [`1_basic_features/memory/10_ipc_memory_withpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/10_ipc_memory_withpid/proc_b.cpp#L59)
- [`1_basic_features/memory/11_ipc_memory_withoutpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/11_ipc_memory_withoutpid/proc_a.cpp#L58)
