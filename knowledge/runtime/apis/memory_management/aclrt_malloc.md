---
type: API
title: aclrtMalloc
description: 在 Device 上分配 size 大小的线性内存，首地址 64 字节对齐；按 policy 选择大页或普通页分配。
tags:
- task.lookup
- topic.implementation.memory_management
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-01_device_memory_malloc_and_free.md
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
# aclrtMalloc

## 功能说明

在 Device 上分配 size 大小的线性内存，首地址 64 字节对齐；按 policy 选择大页或普通页分配。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMallocImpl 内部根据 policy 选择大页/普通页分配策略，最终调用 rtMemAlloc；分配后不对内容清零。

## 函数原型

```c
aclError aclrtMalloc(void **devPtr, size_t size, aclrtMemMallocPolicy policy)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输出 | Device 上已分配内存的指针的指针 |
| size | 输入 | 申请内存的大小，单位 Byte，不能为 0 |
| policy | 输入 | 内存分配规则，见 aclrtMemMallocPolicy；非法值时 size≥2MB 按大页分配 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 分配的内存不会初始化，建议使用前先调用 [aclrtMemset](aclrt_memset.md)
- 内部不会进行隐式 Device 同步或流同步
- policy 仅支持单个枚举项（IPV350 除外，IPV350 支持位或）
- 频繁调用会损耗性能，建议预分配或二次管理

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L46)
- [`0_quickstart/4_custom_kernel_launch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/4_custom_kernel_launch/main.cpp#L52)
- [`1_basic_features/device/0_device_normal/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/0_device_normal/main.cpp#L43)
