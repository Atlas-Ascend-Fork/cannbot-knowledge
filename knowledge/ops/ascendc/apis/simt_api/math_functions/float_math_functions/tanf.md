---
type: API
title: 数学函数tanf
description: 获取输入数据的三角函数正切值。 !
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/tanf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# tanf

## 功能说明

获取输入数据的三角函数正切值。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816325.png)

## 函数原型

```cpp
inline float tanf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入数据的正切值。

-   当`x`为inf时，返回值为nan。
-   当`x`为-inf时，返回值为nan。
-   当`x`为nan时，返回值为nan。

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
    __global__ __launch_bounds__(256) void compute_tanf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = tanf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_tanf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = tanf(x[idx]);
    }

    __global__ __vector__ void run_tanf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_tanf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 0.2553419 0.9315965 3.00957 -5.52038
```


<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“950 FP32 路线直接执行 `tanf(float)`；FP16/BF16 路线严格按 source 顺序执行低精度→FP32、`tanf`、FP32→低精度。”明确三条 950 route 的共同计算 primitive；“函数原型：float tanf(float x)”给出该 primitive 的标量签名。
<!-- cannbot:related:end -->
