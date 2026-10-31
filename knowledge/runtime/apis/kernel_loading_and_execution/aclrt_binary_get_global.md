---
type: API
title: aclrtBinaryGetGlobal
description: 根据全局变量名称获取Device侧全局变量的地址和大小。
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

# aclrtBinaryGetGlobal

## 功能说明

根据全局变量名称获取Device侧全局变量的地址和大小。

## 函数原型

```c
aclError aclrtBinaryGetGlobal(aclrtBinHandle binHandle, const char *name, void **dptr, size_t *size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binHandle | 输入 | 算子二进制句柄。 |
| name | 输入 | 全局变量名称，需与二进制中定义一致。 |
| dptr | 输出 | Device侧地址指针。可为nullptr。 |
| size | 输出 | 变量大小（Byte）。可为nullptr。dptr和size不能同时为nullptr。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

dptr 和 size 不能同时为空；委托 `rtBinaryGetGlobal(binHandle, name, dptr, size)` 到 RTS 层。
