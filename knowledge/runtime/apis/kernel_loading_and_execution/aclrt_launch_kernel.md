---
type: API
title: aclrtLaunchKernel
description: 启动对应算子的计算任务。核函数参数值存放在Device内存中。异步接口。
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

# aclrtLaunchKernel

## 功能说明

启动对应算子的计算任务。核函数参数值存放在Device内存中。异步接口。


内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 构造 rtArgsEx_t（设置 isNoNeedH2DCopy = 1），委托 `rtLaunchKernelByFuncHandleV3(funcHandle, numBlocks, &argsInfo, stream, nullptr)` 到 RTS 层。句柄无效时返回 ACL_ERROR_RT_INVALID_HANDLE。
## 函数原型

```c
aclError aclrtLaunchKernel(aclrtFuncHandle funcHandle, uint32_t numBlocks, const void *argsData, size_t argsSize, aclrtStream stream)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| funcHandle | 输入 | 核函数句柄。 |
| numBlocks | 输入 | 核函数将在几个核上执行。 |
| argsData | 输入 | 核函数入参数据的Device内存地址。 |
| argsSize | 输入 | argsData大小（Byte）。 |
| stream | 输入 | 指定执行任务的Stream。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L124)
