---
type: API
title: aclrtFreeHost
description: "释放 MallocHost 或 MallocHostWithCfg 分配的 Host 内存，不隐式同步或等待任务；需隐式 Device 同步时用 WithDevSync 变体。"
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
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtFreeHost

## 功能说明

释放通过 [aclrtMallocHost](aclrt_malloc_host.md) 或 [aclrtMallocHostWithCfg](aclrt_malloc_host_with_cfg.md) 申请的 Host 内存。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtFreeHostImpl 调用 rtFreeHost 释放。

## 函数原型

```c
aclError aclrtFreeHost(void *hostPtr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| hostPtr | 输入 | 待释放的 Host 内存指针 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 内部不会隐式 Device 同步或流同步，不会等待任务完成

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L128)
- [`1_basic_features/device/2_device_P2P/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/2_device_P2P/main.cpp#L77)
- [`1_basic_features/memory/0_h2h_memory_copy/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/0_h2h_memory_copy/main.cpp#L52)
