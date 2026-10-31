---
type: API
title: aclrtHostRegisterV2
description: "按 flag 注册 Host 内存，可映射或将非锁页内存注册为锁页内存；PINNED 仅适用于非锁页内存，接口不直接返回 Device 指针。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-02_host_memory_management.md
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
---
# aclrtHostRegisterV2

## 功能说明

注册 Host 内存地址，支持多种注册标志。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtHostRegisterV2Impl 将 flag 转换为内部注册标志位后调用 rtHostRegisterV2。

## 函数原型

```c
aclError aclrtHostRegisterV2(void *ptr, uint64_t size, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | Host 内存地址；内核版本约束同 [aclrtHostRegister](aclrt_host_register.md) |
| size | 输入 | 内存大小，单位 Byte |
| flag | 输入 | 注册标志，支持 ACL_HOST_REG_MAPPED / PINNED / IOMEMORY / READONLY 位或 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- ACL_HOST_REG_PINNED 仅对非锁页内存有效；ACL_HOST_REG_IOMEMORY 当前不支持

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp#L71)
