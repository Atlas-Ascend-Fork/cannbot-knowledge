---
type: API
title: aclrtLaunchKernelWithHostArgs
description: 指定任务下发的配置信息，使用Host内存参数值启动计算任务。异步接口。
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

# aclrtLaunchKernelWithHostArgs

## 功能说明

指定任务下发的配置信息，使用Host内存参数值启动计算任务。异步接口。


内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- cfg/placeHolderArray 转为 RTS 类型后委托 `rtsLaunchKernelWithHostArgs(funcHandle, numBlocks, stream, rt_cfg, hostArgs, argsSize, rt_placeHolderArray, placeHolderNum)` 到 RTS 层。
## 函数原型

```c
aclError aclrtLaunchKernelWithHostArgs(aclrtFuncHandle funcHandle, uint32_t numBlocks, aclrtStream stream, aclrtLaunchKernelCfg *cfg, void *hostArgs, size_t argsSize, aclrtPlaceHolderInfo *placeHolderArray, size_t placeHolderNum)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| numBlocks | 输入 | 核函数将在几个核上执行。 |
| stream | 输入 | 指定执行任务的Stream。 |
| cfg | 输入 | 任务下发配置信息。可传NULL。 |
| hostArgs | 输入 | 核函数入参数据的Host内存地址。 |
| argsSize | 输入 | hostArgs大小（Byte）。 |
| placeHolderArray | 输入 | placeholder参数数组。 |
| placeHolderNum | 输入 | placeholder数组大小。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp#L65)
- [`2_advanced_features/kernel/3_binary_get_function_count/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/3_binary_get_function_count/main.cpp#L198)
- [`2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp#L80)
