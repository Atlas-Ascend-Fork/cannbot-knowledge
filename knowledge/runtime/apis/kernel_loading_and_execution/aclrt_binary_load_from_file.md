---
type: API
title: aclrtBinaryLoadFromFile
description: 从文件加载并解析算子二进制文件，输出指向算子二进制的binHandle。AI Core算子需配套 LaunchKernelWithConfig/V2/WithHostArgs 下发。
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

# aclrtBinaryLoadFromFile

## 功能说明

从文件加载并解析算子二进制文件，输出指向算子二进制的binHandle。AI Core算子需配套 LaunchKernelWithConfig/V2/WithHostArgs 下发。


委托 `rtsBinaryLoadFromFile(binPath, rt_options, binHandle)` 到 RTS 层。
## 函数原型

```c
aclError aclrtBinaryLoadFromFile(const char* binPath, aclrtBinaryLoadOptions *options, aclrtBinHandle *binHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| binPath | 输入 | 算子二进制文件（*.o）的绝对路径。AI CPU算子支持传算子信息库文件（*.json）。 |
| options | 输入 | 加载可选参数：`aclrtBinaryLoadOptions`。 |
| binHandle | 输出 | 标识算子二进制的句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

针对某一产品型号编译的算子二进制文件必须在相同型号的产品上使用。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/0_launch_kernel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/0_launch_kernel/main.cpp#L146)
- [`2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp#L42)
- [`2_advanced_features/kernel/3_binary_get_function_count/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/3_binary_get_function_count/main.cpp#L114)
