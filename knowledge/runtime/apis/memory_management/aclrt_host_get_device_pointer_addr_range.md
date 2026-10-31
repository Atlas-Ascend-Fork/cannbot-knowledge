---
type: API
title: aclrtHostGetDevicePointerAddrRange
description: "查询 Host 注册映射的 Device 地址范围数组；addrRange 为空时先获取数组长度，再由调用方分配空间查询。"
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
---
# aclrtHostGetDevicePointerAddrRange

## 功能说明

获取 Host 内存映射成的 Device 内存地址范围。

## 函数原型

```c
aclError aclrtHostGetDevicePointerAddrRange(aclrtAddrRange *addrRange, uint32_t *count)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| addrRange | 输出 | 地址范围数组，由调用方分配内存，见 aclrtAddrRange |
| count | 输入/输出 | addrRange 非空时输入数组长度；为空时输出实际长度 |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 仅 Ascend 950PR 支持，Ascend 950DT 不支持
