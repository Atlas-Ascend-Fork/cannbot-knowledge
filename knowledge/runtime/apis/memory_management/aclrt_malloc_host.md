---
type: API
title: aclrtMallocHost
description: 申请 Host 锁页内存，首地址 64 字节对齐。
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
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMallocHost

## 功能说明

申请 Host 锁页内存，首地址 64 字节对齐。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMallocHostImpl 调用 rtMallocHost 分配锁页内存。

## 函数原型

```c
aclError aclrtMallocHost(void **hostPtr, size_t size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| hostPtr | 输出 | 已分配内存的指针的指针 |
| size | 输入 | 申请内存的大小，单位 Byte，不能为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 分配的内存不会初始化
- 内部不会隐式 Device 同步或流同步
- 过多锁页内存会降低系统性能
- 310P/310B RC/Control CPU 形态下 Host=Device，按普通页申请

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`1_basic_features/device/1_device_multi_thread/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/1_device_multi_thread/main.cpp#L93)
- [`1_basic_features/device/2_device_P2P/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/2_device_P2P/main.cpp#L62)
- [`1_basic_features/memory/0_h2h_memory_copy/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/memory/0_h2h_memory_copy/main.cpp#L31)
