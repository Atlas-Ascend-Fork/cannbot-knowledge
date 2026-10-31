---
type: API
title: aclrtKernelArgsInitByUserMem
description: 根据核函数句柄初始化参数列表（用户管理内存），获取参数列表句柄。需提前通过 aclrtKernelArgsGetMemSize 和 aclrtKernelArgsGetHandleMemSize 获取所需内存大小。
tags:
- task.lookup
- topic.implementation.kernel_launch
- topic.implementation.resource_lifecycle
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

# aclrtKernelArgsInitByUserMem

## 功能说明

根据核函数句柄初始化参数列表（用户管理内存），获取参数列表句柄。需提前通过 [aclrtKernelArgsGetMemSize](aclrt_kernel_args_get_mem_size.md) 和 [aclrtKernelArgsGetHandleMemSize](aclrt_kernel_args_get_handle_mem_size.md) 获取所需内存大小。

## 函数原型

```c
aclError aclrtKernelArgsInitByUserMem(aclrtFuncHandle funcHandle, aclrtArgsHandle argsHandle, void *userHostMem, size_t actualArgsSize)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| argsHandle | 输出 | 参数列表句柄。 |
| userHostMem | 输入 | Host内存地址。 |
| actualArgsSize | 输入 | 内存大小（Byte）。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsKernelArgsInitByUserMem(funcHandle, argsHandle, userHostMem, actualArgsSize)` 到 RTS 层。
