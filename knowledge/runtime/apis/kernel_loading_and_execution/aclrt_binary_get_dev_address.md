---
type: API
title: aclrtBinaryGetDevAddress
description: 获取算子二进制数据在Device上的内存地址及内存大小。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_query
- topic.implementation.api_layer.c_api
status: draft
sources:
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/14_Kernel_loading_and_execution.md
    role: primary
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
    role: header
  - resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/kernel.cpp
    role: implementation
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtBinaryGetDevAddress

## 功能说明

获取算子二进制数据在Device上的内存地址及内存大小。

## 函数原型

```c
aclError aclrtBinaryGetDevAddress(const aclrtBinHandle binHandle, void **binAddr, size_t *binSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binHandle | 输入 | 算子二进制句柄。 |
| binAddr | 输出 | Device上内存地址。懒加载模式下为空指针。 |
| binSize | 输出 | 数据大小（Byte）。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsBinaryGetDevAddress(binHandle, binAddr, &tempBinSize)` 到 RTS 层；返回的 uint32_t 转为 size_t。
