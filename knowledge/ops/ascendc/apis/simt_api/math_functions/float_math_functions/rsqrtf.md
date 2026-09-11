---
type: API
title: Rsqrtf
description: 获取输入数据x的平方根的倒数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/rsqrtf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# rsqrtf

## 功能说明

获取输入数据x的平方根的倒数。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002484776402.png)

## 函数原型

```cpp
inline float rsqrtf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数，输入数据。 |

## 返回值说明

输入数据的平方根的倒数。

-   当x为0时，返回值为inf。
-   当x为inf时，返回值为0。
-   当x为-inf时，返回值为nan。
-   当x为nan时，返回值为nan。

## 约束说明

本接口支持的输入数据范围为x大于等于0，否则返回值为nan。


针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：本接口内部实现使用到了sqrtf，由于sqrtf不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为+inf。


## 需要包含的头文件

使用该接口需要包含`simt_api/math_functions.h`头文件。

```cpp
#include "simt_api/math_functions.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void compute_rsqrtf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = rsqrtf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_rsqrtf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = rsqrtf(x[idx]);
    }

    __global__ __vector__ void run_rsqrtf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_rsqrtf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 1.25, 2.25, 3.25
result: 2 0.8944272 0.6666667 0.5547002
```


<!-- cannbot:related:start -->
## 相关

- [Sqrtf](sqrtf.md)（`related`）：本接口内部实现使用到了sqrtf，由于sqrtf不支持Subnormal场景，当输入x为Subnormal数据时，会导致本接口最终结果为+inf；处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。Rsqrtf 正文明示内部调用 Sqrtf，候选给出 Sqrtf 对 Subnormal 的 flush-to-zero 行为，直接解释 Rsqrtf 在同域返回正无穷的机制。
<!-- cannbot:related:end -->
