---
type: API
title: Signbit
description: 获取输入数据的符号位。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/signbit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# signbit

## 功能说明

获取输入数据的符号位。

## 函数原型

```cpp
inline int signbit(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

返回输入数据的符号位。

-   当`x`为+nan时，返回值为0。
-   当`x`为-nan时，返回值为1。
-   当`x`为inf时，返回值为0。
-   当`x`为-inf时，返回值为1。
-   当`x`为+0时，返回值为0。
-   当`x`为-0时，返回值为1。

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
    __global__ __launch_bounds__(256) void compute_signbit(int *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = signbit(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_signbit_vf(__gm__ int *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = signbit(x[idx]);
    }

    __global__ __vector__ void run_signbit(__gm__ int *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_signbit_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 0 0 0 0
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ForeachMinimumScalar 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_minimum_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `signbit(...)` 的直接调用（第 79 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_minimum_scalar/op_kernel/arch35/foreach_minimum_scalar_simt.h#L79)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
