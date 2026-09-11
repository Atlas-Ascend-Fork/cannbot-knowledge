---
type: API
title: __hadd（整数数学函数）
description: 获取int32类型数据x和y的平均值，避免中间求和溢出。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__hadd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_functions.h
---

# \_\_hadd

## 功能说明

获取int32类型数据x和y的平均值，避免中间求和溢出。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002555143760.png)

## 函数原型

```cpp
int __hadd(int x, int y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |
| y | 输入 | 源操作数。 |

## 返回值说明

输入数据的平均值。

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
    __global__ __launch_bounds__(1024) void KernelHadd(int* dst, int* x, int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __hadd(x[idx], y[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelHadd(__gm__ int* dst, __gm__ int* x, __gm__ int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __hadd(x[idx], y[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [__rhadd（整数数学函数）](_rhadd.md)（`related`）：int32 向上取整平均值函数。获取 int32 类型数据 x 和 y 的向上取整平均值，避免中间求和溢出。；int32 有符号平均值函数。获取 int32 类型数据 x 和 y 的平均值，计算过程避免中间求和溢出（向下取整）。。两接口都避免中间求和溢出，唯一区别是奇数和的向上或向下取整，直接支撑整数平均值舍入选型。
<!-- cannbot:related:end -->
