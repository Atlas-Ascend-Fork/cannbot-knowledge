---
type: API
title: Normcdfinvf
description: 获取输入数据x的标准正态累积分布的逆函数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/normcdfinvf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# normcdfinvf

## 功能说明

获取输入数据x的标准正态累积分布的逆函数。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002533422599.png)

## 函数原型

```cpp
inline float normcdfinvf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

获取输入数据x的标准正态累积分布的逆函数。

-   当`x`为0时，返回值为-inf。
-   当`x`为nan时，返回值为nan。
-   当`x`为1时，返回值为inf。
-   当`x`∉[0,1]时，返回nan。

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
    __global__ __launch_bounds__(256) void compute_normcdfinvf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = normcdfinvf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_normcdfinvf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = normcdfinvf(x[idx]);
    }

    __global__ __vector__ void run_normcdfinvf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_normcdfinvf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：-0.75, -0.25, 0.25, 0.75
result: nan nan -0.6744897 0.6744897
```


<!-- cannbot:related:start -->
## 相关

- [Normcdff](normcdff.md)（`related`）：功能：获取输入数据x的标准正态分布的累积分布函数值。；功能：获取输入数据x的标准正态累积分布的逆函数。两页提供标准正态 CDF 的正向与逆向变换，是概率值和分位点互相转换的同一任务链。
<!-- cannbot:related:end -->
