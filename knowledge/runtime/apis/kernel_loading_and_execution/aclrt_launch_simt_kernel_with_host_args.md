---
type: API
title: aclrtLaunchSIMTKernelWithHostArgs
description: 使用Host内存参数启动SIMT核函数计算任务。异步接口。
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
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtLaunchSIMTKernelWithHostArgs

## 功能说明

使用Host内存参数启动SIMT核函数计算任务。异步接口。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- dim3 转为 rtDim3；委托 `rtLaunchSIMTKernelWithHostArgs(func, rtGridDim, rtBlockDim, dynUbufSize, stream, rtCfg, hostArgs, argsSize, rtPlaceHolder, placeHolderNum)` 到 RTS 层。

## 函数原型

```c
aclError aclrtLaunchSIMTKernelWithHostArgs(void *func, dim3 gridDim, dim3 blockDim, size_t dynUbufSize, aclrtStream stream, aclrtLaunchKernelCfg *cfg, void *hostArgs, size_t argsSize, aclrtPlaceHolderInfo *placeHolderArray, size_t placeHolderNum)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| func | 输入 | 内核函数指针或 aclrtFuncHandle 句柄。 |
| gridDim | 输入 | 线程块网格（三维）。 |
| blockDim | 输入 | 线程块（三维）。 |
| dynUbufSize | 输入 | SIMT算子UB动态内存大小（Byte）。 |
| stream | 输入 | 指定执行任务的Stream。 |
| cfg | 输入 | 任务下发配置信息。可传NULL。 |
| hostArgs | 输入 | 核函数入参数据的Host内存地址。 |
| argsSize | 输入 | hostArgs大小（Byte）。 |
| placeHolderArray | 输入 | placeholder参数数组。 |
| placeHolderNum | 输入 | placeholder数组大小。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

hostArgs需按核函数参数顺序紧凑排列，argsSize需与实际参数总大小一致。
