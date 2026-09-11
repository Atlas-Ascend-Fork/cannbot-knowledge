---
type: API
title: __mul_i32toi64
description: 计算输入32位整数x和y的乘积，返回64位结果。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__mul_i32toi64.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_functions.h
---

# \_\_mul\_i32toi64

## 功能说明

计算输入32位整数x和y的乘积，返回64位结果。

## 函数原型

```cpp
long long __mul_i32toi64(int x, int y)
```

```cpp
unsigned long long __mul_i32toi64(unsigned int x, unsigned int y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数，乘数。 |
| y | 输入 | 源操作数，乘数。 |

## 返回值说明

输入数据x和y乘积的64位结果。

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/device_functions.h`头文件。

```cpp
#include "simt_api/device_functions.h"
```

## 调用示例

-   SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void KernelMul_i32toi64(long long* dst, int* x, int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __mul_i32toi64(x[idx], y[idx]);
    }
    ```

    ```cpp
    __global__ __launch_bounds__(1024) void KernelMul_i32toi64(unsigned long long* dst, unsigned int* x, unsigned int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __mul_i32toi64(x[idx], y[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelMul_i32toi64(__gm__ long long* dst, __gm__ int* x, __gm__ int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __mul_i32toi64(x[idx], y[idx]);
    }
    ```

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelMul_i32toi64(__gm__ unsigned long long* dst, __gm__ unsigned int* x, __gm__ unsigned int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __mul_i32toi64(x[idx], y[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [SimThreadExponential 950 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential_950.md)（`related`）：焦点卡定义“计算输入 32 位整数 x 和 y 的乘积，返回 64 位结果。”，候选算子在 Philox 热路径实际执行“uint64_t res0_u64 = __mul_i32toi64(PHILOX_M4X32_A, counter［0］);”；API 的 64 位乘积合同直接支撑随机数 round 的高低 32 位复用。
<!-- cannbot:related:end -->
