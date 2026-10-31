---
type: API
title: aclrtMemcpy
description: 主机与设备间的同步内存复制，内部按地址自动判定复制方向；跨 Device 复制需先启用 P2P。
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-03_memory_copy_and_set.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-30T07:38:42Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtMemcpy

## 功能说明

实现主机与设备间的同步内存复制。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：

- aclrtMemcpyImpl 根据地址自动判定方向后调用 rtMemcpy 同步复制。

## 函数原型

```c
aclError aclrtMemcpy(void *dst, size_t destMax, const void *src, size_t count, aclrtMemcpyKind kind)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| destMax | 输入 | 目的内存最大长度，单位 Byte |
| src | 输入 | 源内存地址指针 |
| count | 输入 | 内存复制的长度，单位 Byte |
| kind | 输入 | 内存复制类型，系统内部自动判断复制方向 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 本接口同步执行，内部不会隐式 Device 同步或流同步
- 跨 Device 复制需先调用 aclrtDeviceCanAccessPeer 和 aclrtDeviceEnablePeerAccess

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/0_hello_cann/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/0_hello_cann/main.cpp#L49)
- [`0_quickstart/4_custom_kernel_launch/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/4_custom_kernel_launch/main.cpp#L57)
- [`1_basic_features/device/0_device_normal/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/1_basic_features/device/0_device_normal/main.cpp#L46)
