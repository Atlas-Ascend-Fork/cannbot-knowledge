---
type: API
title: aclrtKernelArgsAppend
description: 将参数值追加拷贝到argsHandle指向的参数数据区域。多个参数需按顺序追加。
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

# aclrtKernelArgsAppend

## 功能说明

将参数值追加拷贝到argsHandle指向的参数数据区域。多个参数需按顺序追加。

## 函数原型

```c
aclError aclrtKernelArgsAppend(aclrtArgsHandle argsHandle, void *param, size_t paramSize, aclrtParamHandle *paramHandle)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| argsHandle | 输入 | 参数列表句柄。 |
| param | 输入 | 待追加参数值的Host内存地址。 |
| paramSize | 输入 | 内存大小（Byte）。 |
| paramHandle | 输出 | 参数句柄。 |

## 返回值说明

返回0表示成功，其他值表示失败。

## 约束说明

委托 `rtsKernelArgsAppend(argsHandle, param, paramSize, paramHandle)` 到 RTS 层。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/0_launch_kernel/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/0_launch_kernel/main.cpp#L107)
- [`3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/host_register/0_simple_zero_copy/simple_zero_copy.cpp#L97)
- [`3_memory_advanced/managed_memory/0_uvm_allocate/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/3_memory_advanced/managed_memory/0_uvm_allocate/main.cpp#L120)
