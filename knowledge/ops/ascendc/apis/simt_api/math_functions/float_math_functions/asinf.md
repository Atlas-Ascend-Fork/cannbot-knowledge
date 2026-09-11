---
type: API
title: Asinf
description: 获取输入数据的反正弦值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/asinf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# asinf

## 功能说明

获取输入数据的反正弦值。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002516816355.png)

arcsin\(x\)为反正弦函数的计算。

## 函数原型

```cpp
inline float asinf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入数据的反正弦值。

-   当x为inf时，返回值为nan。
-   当x为-inf时，返回值为nan。
-   当x为nan时，返回值为nan。
-   当x为0时，返回值为0。
-   当x\>1或x<-1时，返回值为nan。

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
    __global__ __launch_bounds__(256) void compute_asinf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = asinf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_asinf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = asinf(x[idx]);
    }

    __global__ __vector__ void run_asinf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_asinf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：-0.75, -0.25, 0.25, 0.75
result: -0.8480784 -0.2526802 0.2526802 0.8480784
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Asin 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/asin_950.md)（`related`）：算子声明的固定版本源码包含对 `asinf(...)` 的直接调用（第 48 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/asin/op_kernel/arch35/asin_dag.h#L48)
- [ForeachAsin 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `asinf(...)` 的直接调用（第 41 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_asin/op_kernel/arch35/foreach_asin_simt.h#L41)
- [InplaceAsin 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `asinf(...)` 的直接调用（第 48 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/asin/op_kernel/arch35/asin_dag.h#L48)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
