---
type: API
title: aclFloatToFloat16
description: 将 float32 类型转换为 aclFloat16 类型。NaN/Inf 按饱和模式处理。
tags:
- task.lookup
- topic.compute.elementwise.type_conversion
- topic.precision
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/24_other_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_base_rt.h
  role: header
source_headers:
- include/external/acl/acl_base_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclFloatToFloat16

## 功能说明

将 float32 转换为 aclFloat16。NaN 和 Inf 按饱和模式处理：均转为 FP16 最大值 65504.0(0x7BFF)，-Inf 转为 -65504.0(0xFBFF)。行为不随 Device 浮点溢出模式变化。

## 函数原型

```c
aclFloat16 aclFloatToFloat16(float value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| value | 输入 | float32 数据 |

## 返回值说明

转换后的 aclFloat16 数据（实际为 uint16_t 存储）。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/2_system_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/2_system_info/main.cpp#L56)
- [`2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp#L54)
- [`2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp#L68)
