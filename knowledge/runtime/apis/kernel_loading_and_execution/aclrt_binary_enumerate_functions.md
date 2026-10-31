---
type: API
title: aclrtBinaryEnumerateFunctions
description: 获取算子二进制中指定数量的核函数句柄。
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

# aclrtBinaryEnumerateFunctions

## 功能说明

获取算子二进制中指定数量的核函数句柄。

内部行为（固定 commit b523035a08ef573b6bc476c8ab2a34733ba069a4 源码结论，不构成跨版本承诺）：

- numFunctions==0 时直接返回成功；委托 `rtBinaryEnumerateFunctions(binHandle, funcHandles, numFunctions)` 到 RTS 层。

## 函数原型

```c
aclError aclrtBinaryEnumerateFunctions(const aclrtBinHandle binHandle, aclrtFuncHandle *funcHandles, uint32_t numFunctions)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binHandle | 输入 | 算子二进制句柄。 |
| funcHandles | 输出 | 核函数句柄数组。 |
| numFunctions | 输入 | 需要获取的句柄数量。0表示不获取。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp#L47)
