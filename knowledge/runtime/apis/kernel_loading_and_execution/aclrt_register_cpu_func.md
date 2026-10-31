---
type: API
title: aclrtRegisterCpuFunc
description: 使用 aclrtBinaryLoadFromData 加载AI CPU算子二进制数据后，注册算子信息得到 funcHandle。仅用于AI CPU算子。
tags:
- task.lookup
- topic.implementation.kernel_launch
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

# aclrtRegisterCpuFunc

## 功能说明

使用 [aclrtBinaryLoadFromData](aclrt_binary_load_from_data.md) 加载AI CPU算子二进制数据后，注册算子信息得到 funcHandle。仅用于AI CPU算子。

## 函数原型

```c
aclError aclrtRegisterCpuFunc(const aclrtBinHandle handle, const char *funcName, const char *kernelName, aclrtFuncHandle *funcHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| handle | 输入 | 算子二进制句柄。 |
| funcName | 输入 | AI CPU算子入口函数。 |
| kernelName | 输入 | AI CPU算子的opType。 |
| funcHandle | 输出 | 函数句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。非AI CPU算子返回 ACL_ERROR_RT_PARAM_INVALID。

## 约束说明

委托 `rtsRegisterCpuFunc(handle, funcName, kernelName, funcHandle)` 到 RTS 层。
