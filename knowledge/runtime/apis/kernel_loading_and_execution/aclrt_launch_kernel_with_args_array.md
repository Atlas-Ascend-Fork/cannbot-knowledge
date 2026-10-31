---
type: API
title: aclrtLaunchKernelWithArgsArray
description: 使用参数数组传递核函数入参并启动计算任务。异步接口。
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

# aclrtLaunchKernelWithArgsArray

## 功能说明

使用参数数组传递核函数入参并启动计算任务。异步接口。


内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- cfg 转为 rtKernelLaunchCfg_t；委托 `rtLaunchKernelWithArgsArray(func, numBlocks, stream, rt_cfg, args)` 到 RTS 层。
## 函数原型

```c
aclError aclrtLaunchKernelWithArgsArray(void *func, uint32_t numBlocks, aclrtStream stream, aclrtLaunchKernelCfg *cfg, void **args)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| func | 输入 | 内核函数指针或 aclrtFuncHandle 句柄。 |
| numBlocks | 输入 | 核函数将在几个核上执行。 |
| stream | 输入 | 指定执行任务的Stream。 |
| cfg | 输入 | 任务下发配置信息。可传NULL。 |
| args | 输入 | 参数数组指针，每个元素指向Host侧参数数据。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

参数数组中的元素顺序需与核函数参数顺序保持一致，大小需与参数数量一致。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/5_fdtd_stencil/fdtd_stencil.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/5_fdtd_stencil/fdtd_stencil.cpp#L57)
