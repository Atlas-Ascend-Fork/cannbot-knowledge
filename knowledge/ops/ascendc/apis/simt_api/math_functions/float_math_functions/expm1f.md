---
type: API
title: Expm1f
description: 指定输入x，获取e的x次方减1。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/expm1f.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# expm1f

## 功能说明

指定输入x，获取e的x次方减1。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002484776378.png)

## 函数原型

```cpp
inline float expm1f(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

e的x次方减1。

-   当x为inf时，返回值为inf。
-   当x为-inf时，返回值为-1.0。
-   当x为nan时，返回值为nan。

## 约束说明


针对Ascend 950PR/Ascend 950DT，本接口不支持输入为Subnormal的场景：本接口内部实现使用到了expf，由于expf不支持Subnormal场景，当输入x处于Subnormal范围内时，返回值为0；当x为较大负数且expf的结果处于Subnormal范围内时，本接口最终结果为-1.0。


## 需要包含的头文件

使用该接口需要包含`simt_api/math_functions.h`头文件。

```cpp
#include "simt_api/math_functions.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void compute_expm1f(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = expm1f(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_expm1f_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = expm1f(x[idx]);
    }

    __global__ __vector__ void run_expm1f(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_expm1f_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 0.2840254 1.117 2.490343 4.754602
```


<!-- cannbot:related:start -->
## 相关

- [Expm1 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/expm1_950.md)（`related`）：算子卡明确“对 `｜x｜ > 2` 直接采用 `expm1f(x)`”；API 卡定义“功能：指定输入x，获取e的x次方减1。”并列出 950 的 subnormal 边界，直接支撑大输入分支及其特殊值核对。
- [InplaceExpm1 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_expm1_950.md)（`related`）：SIMT body 对每个 FP32 元素先保留库函数 `expm1f(x)` 结果。`｜x｜ <= 2` 时使用源码中的 ln2 约化、五阶系数组合及 `exp2f` 重建；`｜x｜ > 2` 时选回 `expm1f`。；函数原型：float expm1f(float x)；算子核心在大幅值分支直接消费 SIMT expm1f，API 卡提供该调用的标量合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ForeachExpm1 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_expm1_950.md)（`related`）：算子声明的固定版本源码包含对 `expm1f(...)` 的直接调用（第 59 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_expm1/op_kernel/arch35/foreach_expm1_simt.h#L59)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
