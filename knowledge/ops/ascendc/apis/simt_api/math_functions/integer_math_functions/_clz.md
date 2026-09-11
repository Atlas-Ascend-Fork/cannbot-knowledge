---
type: API
title: __clz（整数数学函数）
description: 从输入数据的二进制最高有效位开始，返回连续的前导零的位数。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__clz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_functions.h
---

# \_\_clz

## 功能说明

从输入数据的二进制最高有效位开始，返回连续的前导零的位数。

## 函数原型

```cpp
int __clz(int x)
```

```cpp
int __clz(long long x)
```

```cpp
int __clz(long x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

返回输入整数二进制表示中连续高位零的数量。

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
    __global__ __launch_bounds__(1024) void KernelClz(int* dst, int* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __clz(x[idx]);
    }
    ```

    ```cpp
    __global__ __launch_bounds__(1024) void KernelClz(int* dst, long long* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __clz(x[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelClz(__gm__ int* dst, __gm__ int* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __clz(x[idx]);
    }
    ```

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelClz(__gm__ int* dst, __gm__ long long* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __clz(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [asc_clz（标量计算）](../../../simd_api/c_api/scalar_compute/scalar_bit/asc_clz.md)（`same_topic`）：计算一个uint64_t类型整数在二进制表示下的前导零个数；前导零计数函数。从输入数据的二进制最高有效位开始，返回连续的前导零的位数。。asc_clz 与 SIMT __clz 都从最高有效位计算连续零数，但执行模型和参数重载不同，关系可帮助按 Scalar/SIMT 路线选型。
<!-- cannbot:related:end -->
