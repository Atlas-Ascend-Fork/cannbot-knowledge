---
type: API
title: aclrtMallocPhysical
description: 申请 Host 或 Device 物理内存，返回物理内存 handle，可配合虚拟内存管理接口使用。
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMallocPhysical

## 功能说明

申请 Host 或 Device 物理内存，返回物理内存 handle，可配合虚拟内存管理接口使用。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMallocPhysicalImpl 将 prop 转换为 rtDrvMemProp_t 后调用 rtMemAllocPhysical。

## 函数原型

```c
aclError aclrtMallocPhysical(aclrtDrvMemHandle *handle, size_t size, const aclrtPhysicalMemProp *prop, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输出 | 存放物理内存信息的 handle |
| size | 输入 | 物理内存大小，建议按粒度对齐 |
| prop | 输入 | 物理内存属性，见 aclrtPhysicalMemProp |
| flags | 输入 | 预留，固定设置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 支持多种内存属性：NORMAL / HUGE / HUGE1G / P2P_NORMAL / P2P_HUGE / HBM 等

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/12_cross_server_physical_memory_sharing_withoutpid/server.cpp#L60)
- [`1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/7_physical_memory_sharing_withpid/proc_a.cpp#L48)
- [`1_basic_features/memory/8_physical_memory_sharing_withoutpid/proc_a.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/8_physical_memory_sharing_withoutpid/proc_a.cpp#L48)
