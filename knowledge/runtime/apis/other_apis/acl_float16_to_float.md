---
type: API
title: aclFloat16ToFloat
description: 将 aclFloat16 类型转换为 float32 类型。NaN/Inf 不保留语义。
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

# aclFloat16ToFloat

## 功能说明

将 aclFloat16 转换为 float32。NaN 和 Inf 等特殊值不保留语义：FP16 +Inf(0x7C00) -> 65536.0，-Inf(0xFC00) -> -65536.0，NaN(0x7E00) -> 98304.0。该行为不随 Device 浮点溢出模式变化。

## 函数原型

```c
float aclFloat16ToFloat(aclFloat16 value)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- |:---:| --- |
| value | 输入 | aclFloat16 类型数据 |

## 返回值说明

转换后的 float32 数据。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`0_quickstart/2_system_info/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/0_quickstart/2_system_info/main.cpp#L57)
- [`2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/2_binary_enumerate_functions/main.cpp#L69)
- [`2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/2_advanced_features/kernel/6_memory_loaded_vector_add/main.cpp#L84)
