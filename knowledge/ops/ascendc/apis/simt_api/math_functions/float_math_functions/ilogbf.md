---
type: API
title: Ilogbf
description: 计算以2为底输入数据的对数，对结果向下取整返回整数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/ilogbf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# ilogbf

## 功能说明

计算以2为底，输入数据绝对值的对数，并对结果向下取整，返回整数。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002484776384.png)

## 函数原型

```cpp
inline int ilogbf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

对于有限非零值，返回以2为底的x的绝对值的对数，并向下取整后的整数值。

特殊取值场景下的返回值如下表所示。

| 输入值x | 返回值 |
| --- | --- |
| +0 | ASCRT_MIN_VAL_S |
| -0 | ASCRT_MIN_VAL_S |
| inf | ASCRT_MAX_VAL_S |
| -inf | ASCRT_MAX_VAL_S |
| nan | ASCRT_MIN_VAL_S |

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
    __global__ __launch_bounds__(256) void compute_ilogbf(int *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = ilogbf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_ilogbf_vf(__gm__ int *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = ilogbf(x[idx]);
    }

    __global__ __vector__ void run_ilogbf(__gm__ int *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_ilogbf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: -2 -1 0 0
```


<!-- cannbot:related:start -->
## 相关

- [Logbf](logbf.md)（`related`）：功能：计算以2为底，输入数据的对数，并对结果向下取整，返回整数。；功能：计算以2为底，输入数据的对数，并对结果向下取整，返回浮点数。。两接口共享有限非零输入的指数提取语义，但返回类型和零、无穷、NaN 的特殊值合同不同，选型时需成对比较。
<!-- cannbot:related:end -->
