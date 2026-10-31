---
type: API
title: aclrtIpcMemImportByKey
description: "按 IPC key 导入共享内存，返回当前进程的 Device 地址；可选择开启 P2P，导入前须保证共享内存未释放。"
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
# aclrtIpcMemImportByKey

## 功能说明

导入 IPC 共享内存 key，返回本进程可用的 Device 地址。

## 函数原型

```c
aclError aclrtIpcMemImportByKey(void **devPtr, const char *key, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | Device 内存地址指针 |
| key | 输入 | 共享内存 key |
| flags | 输入 | 是否开启 P2P 数据交互 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 调用前需保证共享内存存在，不能提前释放

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/10_ipc_memory_withpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/10_ipc_memory_withpid/proc_b.cpp#L48)
- [`1_basic_features/memory/11_ipc_memory_withoutpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/11_ipc_memory_withoutpid/proc_b.cpp#L38)
- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_b.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_b.cpp#L54)
