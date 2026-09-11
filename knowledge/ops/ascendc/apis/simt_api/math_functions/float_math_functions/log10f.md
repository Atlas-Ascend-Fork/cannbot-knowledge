---
type: API
title: Log10f
description: 获取以10为底输入数据的对数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/log10f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# log10f

## 功能说明

获取以10为底，输入数据的对数。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816341.png)

## 函数原型

```cpp
inline float log10f(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

以10为底的x的对数。

-   当x为inf时，返回值为inf。
-   当x为-inf时，返回值为nan。
-   当x为nan时，返回值为nan。

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
    __global__ __launch_bounds__(256) void compute_log10f(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = log10f(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_log10f_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = log10f(x[idx]);
    }

    __global__ __vector__ void run_log10f(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_log10f_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：1, 2, 3, 4
result: 0 0.30103 0.4771213 0.60206
```


<!-- cannbot:related:start -->
## 相关

- [ForeachLog10 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_log10_950.md)（`related`）：获取以10为底，输入数据的对数；R-001 FLOAT `log10f`；950 ForeachLog10 的 FLOAT route 直接消费该 SIMT 函数。
<!-- cannbot:related:end -->
