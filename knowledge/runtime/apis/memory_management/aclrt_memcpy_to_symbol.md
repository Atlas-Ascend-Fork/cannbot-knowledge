---
type: API
title: aclrtMemcpyToSymbol
description: "C 接口按符号地址及偏移，将 Host 数据同步写入 Device 变量；仅支持 H2D 或 DEFAULT，沿用混合编译符号访问约束。"
tags:
- task.lookup
- topic.data_movement.data_copy
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/11-11_device_variable_memory_operation.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/memory.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310p'
---
# aclrtMemcpyToSymbol

## 功能说明

同步将 Host 数据复制到 Device 变量。

## 函数原型

```c
aclError aclrtMemcpyToSymbol(const void *symbol, const void *src, size_t count, size_t offset, aclrtMemcpyKind kind)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| symbol | 输入 | Device 变量的地址 |
| src | 输入 | 源内存地址指针 |
| count | 输入 | 复制长度 |
| offset | 输入 | 变量地址偏移 |
| kind | 输入 | 仅支持 HOST_TO_DEVICE 和 DEFAULT |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 约束同 [aclrtGetSymbolAddress](aclrt_get_symbol_address.md)

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/5_fdtd_stencil/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/5_fdtd_stencil/main.cpp#L64)
