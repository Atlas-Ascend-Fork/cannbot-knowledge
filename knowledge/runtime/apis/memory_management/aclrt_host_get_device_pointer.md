---
type: API
title: aclrtHostGetDevicePointer
description: "从已注册的 Host 指针查询 Device 映射地址；所得地址供 Device 访问，不能用于内存复制等内存操作。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
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
# aclrtHostGetDevicePointer

## 功能说明

获取由 [aclrtHostRegister](aclrt_host_register.md) 或 [aclrtHostRegisterV2](aclrt_host_register_v2.md) 注册映射的 Device 地址。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtHostGetDevicePointerImpl 查询注册表获取对等映射地址。

## 函数原型

```c
aclError aclrtHostGetDevicePointer(void *pHost, void **pDevice, uint32_t flag)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| pHost | 输入 | 已注册映射的 Host 内存地址 |
| pDevice | 输出 | Host 内存映射成的 Device 内存地址 |
| flag | 输入 | 预留参数，固定配置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 映射后的 Device 地址不能用于内存复制等内存操作

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp#L73)
