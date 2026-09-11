---
type: API
title: __hgtu
description: 比较两个bfloat16类型数据，当第一个数据大于第二个数据时，返回true。若任一输入为nan，返回true。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_compare_functions/__hgtu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_hgtu

## 功能说明

比较两个bfloat16类型数据，当第一个数据大于第二个数据时，返回true。若任一输入为nan，返回true。

## 函数原型

```cpp
bool __hgtu(bfloat16_t x, bfloat16_t y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |
| y | 输入 | 源操作数。 |

## 返回值说明

比较输入的第一个数是否大于第二个数的结果。

-   true：第一个数大于第二个数，或者任一输入为nan。
-   false：第一个数小于或等于第二个数。

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_bf16.h`头文件。

```cpp
#include "simt_api/asc_bf16.h"
```

## 调用示例

-   SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void KernelHgtu(bool* dst, bfloat16_t* x, bfloat16_t* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __hgtu(x[idx], y[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelHgtu(__gm__ bool* dst, __gm__ bfloat16_t* x, __gm__ bfloat16_t* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __hgtu(x[idx], y[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__hgt](_hgt.md)（`related`）：比较两个bfloat16类型数据，当第一个数据大于第二个数据时，返回true。若任一输入为nan，返回true。；比较两个bfloat16类型数据，仅当第一个数据大于第二个数据时，返回true。两页是同一 bfloat16 大于比较的 unordered 与 ordered 选择，NaN 返回差异是实现正确性所需的关键决策。
<!-- cannbot:related:end -->
