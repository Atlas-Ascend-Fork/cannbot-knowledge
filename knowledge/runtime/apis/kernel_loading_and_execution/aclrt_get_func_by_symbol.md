---
type: API
title: aclrtGetFuncBySymbol
description: 根据核函数名（__global__声明的函数名）获取核函数句柄。仅用于Ascend C自定义算子Host+Device混合编译场景。
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
- '310p'
source_headers:
- include/external/acl/acl_rt.h
---

# aclrtGetFuncBySymbol

## 功能说明

根据核函数名（__global__声明的函数名）获取核函数句柄。仅用于Ascend C自定义算子Host+Device混合编译场景。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- 委托 `rtGetFuncBySymbol(symbol, funcHandle)` 到 RTS 层。

## 函数原型

```c
aclError aclrtGetFuncBySymbol(const void *symbol, aclrtFuncHandle *funcHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| symbol | 输入 | 核函数名。 |
| funcHandle | 输出 | 核函数句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

仅支持算子静态Shape场景，仅支持AI Core算子。核函数句柄仅在当前Device有效，切换Device后需重新获取。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/5_fdtd_stencil/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/5_fdtd_stencil/main.cpp#L44)
