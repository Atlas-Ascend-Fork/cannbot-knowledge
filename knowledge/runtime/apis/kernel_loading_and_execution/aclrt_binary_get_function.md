---
type: API
title: aclrtBinaryGetFunction
description: 根据核函数名称查找对应的核函数，使用 funcHandle 表达。首次调用会将二进制数据拷贝至当前Context对应的Device上。
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

# aclrtBinaryGetFunction

## 功能说明

根据核函数名称查找对应的核函数，使用 funcHandle 表达。首次调用会将二进制数据拷贝至当前Context对应的Device上。

## 函数原型

```c
aclError aclrtBinaryGetFunction(const aclrtBinHandle binHandle, const char *kernelName, aclrtFuncHandle *funcHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binHandle | 输入 | 算子二进制句柄。 |
| kernelName | 输入 | 核函数名称。 |
| funcHandle | 输出 | 核函数句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsFuncGetByName(binHandle, kernelName, funcHandle)` 到 RTS 层。当前不支持多Kernel，tilingKey 固定使用0。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/0_launch_kernel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/0_launch_kernel/main.cpp#L148)
- [`2_advanced_features/kernel/3_binary_get_function_count/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/3_binary_get_function_count/main.cpp#L133)
- [`2_advanced_features/kernel/4_launch_blocking/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/4_launch_blocking/main.cpp#L98)
