---
type: API
title: aclrtMemcpyFromSymbol
description: "C 接口按符号地址及偏移，将 Device 变量同步复制到 Host；仅支持 D2H 或 DEFAULT，offset+count 不得越过变量大小。"
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-11_device_variable_memory_operation.md
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
- '310p'
---
# aclrtMemcpyFromSymbol

## 功能说明

同步将 Device 变量数据复制到 Host。

## 函数原型

```c
aclError aclrtMemcpyFromSymbol(void *dst, size_t dstMax, const void *symbol, size_t count, size_t offset, aclrtMemcpyKind kind)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| dst | 输入 | 目的内存地址指针 |
| dstMax | 输入 | 目的内存最大长度 |
| symbol | 输入 | Device 变量的地址 |
| count | 输入 | 复制长度，需满足 offset+count ≤ 变量大小 |
| offset | 输入 | 变量地址偏移 |
| kind | 输入 | 复制类型，仅支持 DEVICE_TO_HOST 和 DEFAULT |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 约束同 [aclrtGetSymbolAddress](aclrt_get_symbol_address.md)
