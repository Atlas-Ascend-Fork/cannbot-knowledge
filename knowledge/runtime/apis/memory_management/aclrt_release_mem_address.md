---
type: API
title: aclrtReleaseMemAddress
description: "释放 ReserveMemAddress 预留的虚拟地址空间；仍映射物理内存时，须先调用 UnmapMem 解除映射。"
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
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtReleaseMemAddress

## 功能说明

释放通过 [aclrtReserveMemAddress](aclrt_reserve_mem_address.md) 申请的虚拟内存。

## 函数原型

```c
aclError aclrtReleaseMemAddress(void *virPtr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtr | 输入 | 待释放的虚拟内存地址指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 若虚拟内存与物理内存存在映射，需先调用 [aclrtUnmapMem](aclrt_unmap_mem.md) 取消映射

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/client.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/client.cpp#L125)
- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp#L147)
- [`1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp#L103)
