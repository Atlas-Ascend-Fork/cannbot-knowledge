---
type: API
title: __hmin
description: 获取两个输入数据中的最小值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_compare_functions/__hmin.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_fp16.h
---

# \_\_hmin

## 功能说明

获取两个输入数据中的最小值。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002501694974.png)

## 函数原型

```cpp
inline half __hmin(half x, half y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |
| y | 输入 | 源操作数。 |

## 返回值说明

两个输入数据中的最小值。本接口受全局饱和寄存器的影响，特殊值如下：

| x值 | y值 | 返回值 |
| --- | --- | --- |
| ±0 | ±0 | 0 |
| nan | normal | normal |
| nan | nan | nan |
| -inf | normal | -inf |
| normal | -inf | -inf |
| inf | normal | normal |
| normal | inf | normal |

## 约束说明

无

## 需要包含的头文件

使用half类型接口需要包含`simt_api/asc_fp16.h`头文件。

```cpp
#include "simt_api/asc_fp16.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel_min(half* dst, half* x, half* y, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __hmin(x[idx], y[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel_min(__gm__ half* dst, __gm__ half* x, __gm__ half* y, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __hmin(x[idx], y[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__hmin_nan](_hmin_nan.md)（`same_topic`）：返回值：两个输入数据中的最小值。本接口受全局饱和寄存器的影响，。特殊值：±0→0；nan→normal；nan→nan；-inf→-inf；(normal,-inf)→-inf；inf→normal；(normal,inf)→normal。；返回值：两个输入数据中的最小值。特殊值：-0→x；(+0,-0)→y；nan→nan；(任意值,nan)→nan；-inf→-inf；(任意值,-inf)→-inf；inf→y。。两接口均求 half 标量最小值，但 __hmin_nan 明确传播任一 NaN，而 __hmin 的特殊值结果受全局饱和寄存器及操作数组合影响。
<!-- cannbot:related:end -->
