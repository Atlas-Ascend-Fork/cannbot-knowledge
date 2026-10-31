---
type: API
title: aclrtMemManagedPrefetchAsync
description: "C++ 模板向指定 Stream 下发单段 UVM 预取，长度须 2MB 对齐；成功仅表示下发，完成需同步等待。"
tags:
- task.lookup
- topic.implementation.memory_management
- topic.data_movement
- topic.implementation.api_layer.cpp_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/26_cpp_extension_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt_api.h
  role: header
source_headers:
- include/external/acl/acl_rt_api.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- a2
---

# aclrtMemManagedPrefetchAsync

## 功能说明

实现统一虚拟内存（Unified Virtual Memory, UVM）的预取。
本接口操作的内存必须是通过[aclrtMemAllocManaged](aclrt_mem_alloc_managed.md)接口分配的。本接口是异步接口，调用接口成功仅表示任务下发成功，不表示任务执行成功，调用本接口后，需调用同步等待接口（例如，aclrtSynchronizeStream）确保内存预取的任务已执行完成。
本接口为封装接口，仅适用于C++程序，接口内部调用C接口aclrtMemManagedPrefetchAsync。

## 函数原型

```cpp
template <typename T>
aclError aclrtMemManagedPrefetchAsync(const T *ptr, size_t size, aclrtMemManagedLocation location, uint32_t flags, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| ptr | 输入 | 待预取的内存地址，地址范围必须在UVM内存范围之内，即[0x90000000000ULL, 0x90000000000ULL+3TB)。 |
| size | 输入 | 待预取的内存长度，单位Byte，要求2MB对齐。取值范围为(0, 3TB]。 |
| location | 输入 | 物理内存的位置信息，location参数包含id和type两个成员。类型定义请参见aclrtMemManagedLocation。 |
| flags | 输入 | 预留参数。当前固定配置为0。 |
| stream | 输入 | 指定执行内存预取任务的stream。类型定义请参见aclrtStream。 |

## 返回值说明

返回0表示成功，返回其他值表示失败，请参见aclError。
