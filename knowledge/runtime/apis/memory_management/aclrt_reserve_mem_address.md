---
type: API
title: aclrtReserveMemAddress
description: 预留虚拟内存，用于后续映射物理内存。
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
updated_at: '2026-10-31T02:47:07Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtReserveMemAddress

## 功能说明

预留虚拟内存，用于后续映射物理内存。

## 函数原型

```c
aclError aclrtReserveMemAddress(void **virPtr, size_t size, size_t alignment, void *expectPtr, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| virPtr | 输出 | 已分配的虚拟内存地址的指针的指针 |
| size | 输入 | 虚拟内存大小，单位 Byte，不能为 0 |
| alignment | 输入 | 虚拟地址对齐值，当前只能设置为 0 |
| expectPtr | 输入 | 传 nullptr 时由系统自动分配；传非 nullptr 时指定期望的起始地址（试验特性） |
| flags | 输入 | 预留参数，建议固定配置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅当 `expectPtr` 非 `nullptr`、由用户指定起始地址时，该功能为试验特性，后续版本可能变更，不支持应用于生产环境中。
- 950 仅支持 expectPtr=nullptr
- 预留的虚拟内存单进程仅支持 [aclrtMemcpyAsync](aclrt_memcpy_async.md) 跨 Device 复制

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/client.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/client.cpp#L98)
- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp#L65)
- [`1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp#L53)
