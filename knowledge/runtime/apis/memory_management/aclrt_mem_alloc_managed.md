---
type: API
title: aclrtMemAllocManaged
description: "申请按 2MB 向上对齐的 UVM 内存，通过缺页机制迁移，访问时建立页表；单进程上限 3TB。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-05_unified_addressing.md
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
- a3
- a2
---
# aclrtMemAllocManaged

## 功能说明

申请统一虚拟内存（UVM），通过缺页机制自动管理迁移。

## 函数原型

```c
aclError aclrtMemAllocManaged(void **ptr, uint64_t size, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输出 | 已分配 UVM 内存的指针 |
| size | 输入 | 内存大小，单位 Byte，不能为 0，单进程最大 3TB |
| flag | 输入 | 内存标识，仅支持 ACL_RT_MEM_ATTACH_GLOBAL |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 分配大小向上按 2MB 对齐
- 仅在访问时建立页表映射

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/managed_memory/0_uvm_allocate/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/managed_memory/0_uvm_allocate/main.cpp#L70)
