---
type: API
title: aclrtIpcMemGetExportKey
description: "将 Device 地址对应的内存导出为 IPC key，支持开关进程白名单校验；key 缓冲区长度固定为 65。"
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
# aclrtIpcMemGetExportKey

## 功能说明

将 Device 内存设置为 IPC 共享内存，返回共享 key。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtIpcMemGetExportKeyImpl 调用 rtIpcMemGetExportKey 生成 key。

## 函数原型

```c
aclError aclrtIpcMemGetExportKey(void *devPtr, size_t size, char *key, size_t len, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输入 | Device 内存地址 |
| size | 输入 | 内存大小，单位 Byte |
| key | 输出 | 共享内存 key（字符数组，长度固定 65） |
| len | 输入 | key 长度，固定配置为 65 |
| flags | 输入 | 是否启用进程白名单校验 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 不同 Device 上跨进程使用 IPC 时，内存复制有限制

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/10_ipc_memory_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/10_ipc_memory_withpid/proc_a.cpp#L46)
- [`1_basic_features/memory/11_ipc_memory_withoutpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/11_ipc_memory_withoutpid/proc_a.cpp#L46)
- [`2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/notify/0_ipc_notify_withpid/proc_a.cpp#L51)
