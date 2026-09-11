---
type: API
title: Lgammaf
description: 获取输入数据x伽马值的绝对值并求自然对数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/lgammaf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# lgammaf

## 功能说明

获取输入数据x伽马值的绝对值并求自然对数。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002484776424.png)

## 函数原型

```cpp
inline float lgammaf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入数据的伽马值的绝对值并求自然对数。

-   当x为0时，返回值为inf。
-   当x为inf时，返回值为inf。
-   当x为-inf时，返回值为inf。
-   当x为nan时，返回值为nan。
-   若返回值超出float最大范围，返回值为inf。
-   若返回值超出float最小范围，返回值为-inf。

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/math_functions.h`头文件。

```cpp
#include "simt_api/math_functions.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void compute_lgammaf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = lgammaf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_lgammaf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = lgammaf(x[idx]);
    }

    __global__ __vector__ void run_lgammaf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_lgammaf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 1.288023 0.203281 -0.09827184 -0.08440112
```


<!-- cannbot:related:start -->
## 相关

- [Lgamma](../../../simd_api/adv_api/math_compute/lgamma_interface/lgamma.md)（`same_topic`）：功能：获取输入数据x伽马值的绝对值并求自然对数。；按元素计算x的gamma函数绝对值的自然对数（lgamma(x) = ln(｜gamma(x)｜)）。模板参数T支持half/float。两卡核心数学对象均为 lgamma，分别覆盖 SIMT 标量 float 与高阶 LocalTensor 逐元素接口。
<!-- cannbot:related:end -->
