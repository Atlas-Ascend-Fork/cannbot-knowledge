---
type: API
title: aclrtIpcMemSetImportPid
description: "为已导出的 IPC 内存 key 设置可导入进程的 PID 数组，配合 IpcMemGetExportKey 的白名单校验使用。"
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
# aclrtIpcMemSetImportPid

## 功能说明

设置 IPC 共享内存的进程白名单。

## 函数原型

```c
aclError aclrtIpcMemSetImportPid(const char *key, int32_t *pid, size_t num)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| key | 输入 | 通过 [aclrtIpcMemGetExportKey](aclrt_ipc_mem_get_export_key.md) 获取的内存 key |
| pid | 输入 | 白名单进程 ID 数组 |
| num | 输入 | 白名单进程数量 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/10_ipc_memory_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/10_ipc_memory_withpid/proc_a.cpp#L55)
