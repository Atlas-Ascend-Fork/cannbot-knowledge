---
type: API
title: aclrtLaunchKernelWithConfig
description: 使用 aclrtArgsHandle 参数列表句柄组装入参，指定配置信息并启动计算任务。AI Core算子需配套 aclrtBinaryLoadFromFile。异步接口。
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

# aclrtLaunchKernelWithConfig

## 功能说明

使用 aclrtArgsHandle 参数列表句柄组装入参，指定配置信息并启动计算任务。AI Core算子需配套 [aclrtBinaryLoadFromFile](aclrt_binary_load_from_file.md)。异步接口。


内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 校验 reserve==nullptr；cfg 转为 rtKernelLaunchCfg_t；委托 `rtsLaunchKernelWithConfig(funcHandle, numBlocks, stream, rt_cfg, argsHandle, reserve)` 到 RTS 层。
## 函数原型

```c
aclError aclrtLaunchKernelWithConfig(aclrtFuncHandle funcHandle, uint32_t numBlocks, aclrtStream stream, aclrtLaunchKernelCfg *cfg, aclrtArgsHandle argsHandle, void *reserve)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| numBlocks | 输入 | 核函数将在几个核上执行。 |
| stream | 输入 | 指定执行任务的Stream。 |
| cfg | 输入 | 任务下发配置信息。可传NULL。 |
| argsHandle | 输入 | 参数列表句柄。 |
| reserve | 输入 | 预留参数，固定传NULL。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/0_launch_kernel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/0_launch_kernel/main.cpp#L167)
- [`3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp#L118)
- [`3_memory_advanced/managed_memory/0_uvm_allocate/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/managed_memory/0_uvm_allocate/main.cpp#L151)
