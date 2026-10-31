---
type: API
title: aclrtGetSymbolSize
description: "C 接口以 Device 变量的符号地址查询其占用字节数，沿用 GetSymbolAddress 的 Ascend C 混合编译约束。"
tags:
- task.lookup
- topic.implementation.resource_query
- topic.memory
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
# aclrtGetSymbolSize

## 功能说明

获取 Device 变量占用的内存大小。

## 函数原型

```c
aclError aclrtGetSymbolSize(const void *symbol, size_t *size)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| symbol | 输入 | Device 变量的地址 |
| size | 输出 | Device 变量的大小，单位 Byte |

## 返回值说明

返回 0 表示成功，返回其他值表示失败，参见 aclError。

## 约束说明

- 约束同 [aclrtGetSymbolAddress](aclrt_get_symbol_address.md)

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`2_advanced_features/kernel/5_fdtd_stencil/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/5_fdtd_stencil/main.cpp#L58)
