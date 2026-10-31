---
type: API
title: aclrtKernelArgsGetPlaceHolderBuffer
description: 根据内存大小获取paramHandle占位符指向的内存地址。用户管理数据但无需管理生命周期。
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

# aclrtKernelArgsGetPlaceHolderBuffer

## 功能说明

根据内存大小获取paramHandle占位符指向的内存地址。用户管理数据但无需管理生命周期。

## 函数原型

```c
aclError aclrtKernelArgsGetPlaceHolderBuffer(aclrtArgsHandle argsHandle, aclrtParamHandle paramHandle, size_t dataSize, void **bufferAddr)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| argsHandle | 输入 | 参数列表句柄。 |
| paramHandle | 输入 | 参数句柄。 |
| dataSize | 输入 | 内存大小。 |
| bufferAddr | 输出 | 占位符指向的内存地址。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsKernelArgsGetPlaceHolderBuffer(argsHandle, paramHandle, dataSize, bufferAddr)` 到 RTS 层。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/0_launch_kernel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/0_launch_kernel/main.cpp#L127)
