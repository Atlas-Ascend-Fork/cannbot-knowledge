---
type: API
title: aclrtMemP2PMap
description: "为同进程两个 Device 的内存建立跨设备页表映射；须先用 DeviceEnablePeerAccess 开启 P2P 数据交互。"
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
- '950'
- a3
- a2
- '310p'
- '910'
---
# aclrtMemP2PMap

## 功能说明

建立同一进程内两个 Device 间的内存页表映射，实现跨 Device 访问。

## 函数原型

```c
aclError aclrtMemP2PMap(void *devPtr, size_t size, int32_t dstDevId, uint64_t flags)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| devPtr | 输入 | 共享内存提供方的 Device 内存地址 |
| size | 输入 | 内存大小，单位 Byte |
| dstDevId | 输入 | 共享内存使用方的 Device ID |
| flags | 输入 | 预留，固定设置为 0 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 需先调用 aclrtDeviceEnablePeerAccess 开启数据交互
