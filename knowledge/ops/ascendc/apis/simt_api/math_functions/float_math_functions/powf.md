---
type: API
title: 数学函数powf
description: 获取输入数据x的y次幂。 !
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/powf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# powf

## 功能说明

获取输入数据x的y次幂。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816365.png)

## 函数原型

```cpp
inline float powf(float x, float y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数，幂计算的底数。 |
| y | 输入 | 源操作数，幂计算的指数。 |

## 返回值说明

x的y次幂的结果。

-   若x^y超出float最大范围，返回值为inf。
-   若x为±0，y小于0并且为奇数，返回值为±inf。
-   若x为±0，y小于0并且不为奇数，返回值为inf。
-   若x为±0，y大于0并且为奇数，返回值为±0。
-   若x为±0，y大于0并且不为奇数，返回值为0。
-   若x为-1，y为±inf，返回值为1。
-   若x为1，y为任意值（包括nan），返回值为1。
-   若y为±0，x为任意值（包括nan），返回值为1。
-   若x小于0，y不为整数，返回值为nan。
-   若|x|<1，y为-inf，返回值为inf。
-   若|x|\>1，y为-inf，返回值为0。
-   若|x|<1，y为inf，返回值为0。
-   若|x|\>1，y为inf，返回值为inf。
-   若x为-inf，y小于0并且为奇数，返回值为-0。
-   若x为-inf，y小于0并且不为奇数，返回值为0。
-   若x为-inf，y大于0并且为奇数，返回值为-inf。
-   若x为-inf，y大于0并且不为奇数，返回值为inf。
-   若x为inf，y小于0，返回值为0。
-   若x为inf，y大于0，返回值为inf。
-   在如下边界场景，返回值为nan。
    -   x为nan，y不为0。
    -   y为nan，x不为1。
    -   x、y均为nan

## 约束说明


针对Ascend 950PR/Ascend 950DT，本接口不支持Subnormal场景：处于Subnormal范围内的输入和输出值，都会被刷新为保留符号的0。


## 需要包含的头文件

使用该接口需要包含`simt_api/math_functions.h`头文件。

```cpp
#include "simt_api/math_functions.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void compute_powf(float *result, const float *x, const float *y, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = powf(x[idx], y[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_powf_vf(__gm__ float *result, __gm__ const float *x, __gm__ const float *y, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = powf(x[idx], y[idx]);
    }

    __global__ __vector__ void run_powf(__gm__ float *result, __gm__ const float *x, __gm__ const float *y, uint32_t count)
    {
        asc_vf_call<compute_powf_vf>(dim3(256), result, x, y, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
y：1.25, 2.25, 3.25, 4.25
result: 0.176777 0.523465 2.065178 10.787274
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ForeachPowScalar 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_pow_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `powf(...)` 的直接调用（第 128 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_pow_scalar/op_kernel/arch35/foreach_pow_scalar_simt.h#L128)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
