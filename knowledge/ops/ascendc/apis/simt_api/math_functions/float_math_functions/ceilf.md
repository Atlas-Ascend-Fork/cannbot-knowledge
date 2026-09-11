---
type: API
title: Ceilf
description: 获取大于或等于输入数据的最小整数值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/ceilf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# ceilf

## 功能说明

获取大于或等于输入数据的最小整数值。

## 函数原型

```cpp
inline float ceilf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

大于或等于输入数据的最小整数值。特别场景说明如下：

-   当`x`为nan时，返回值为nan。
-   当`x`为inf时，返回值为inf。
-   当`x`为-inf时，返回值为-inf。

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
    __global__ __launch_bounds__(256) void compute_ceilf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = ceilf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_ceilf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = ceilf(x[idx]);
    }

    __global__ __vector__ void run_ceilf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_ceilf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 1 1 2 2
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 84 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_simt_hw.h#L84)
- [UpsampleLinear1dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_linear_1d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 80 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_linear_grad/op_kernel/arch35/resize_linear_grad_simt_determine.h#L80)
- [UpsampleNearest2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_nearest_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_nearest_neighbor_v2_grad/op_kernel/arch35/resize_nearest_neighbor_v2_grad_simt_determine.h#L88)
- [UpsampleNearestExact2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_nearest_exact_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 37 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_nearest_exact2d_grad/op_kernel/arch35/upsample_nearest_exact2d_grad_simt_base.h#L37)
- [UpsampleNearestExact3dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_nearest_exact_3d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 37 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_nearest3d_grad/op_kernel/arch35/upsample_nearest3d_grad_simt_base.h#L37)
- [RoiPoolingWithArgMax 950 ACLNN 算子知识](../../../../operators/aclnn/cv/objdetect/roi_pooling_with_arg_max_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 53 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_pooling_with_arg_max/op_kernel/arch35/roi_pooling_with_arg_max_simt.h#L53)
- [ResizeBilinear 950 Direct Invoke 算子知识](../../../../operators/direct/cv/image/resize_bilinear_950.md)（`related`）：算子声明的固定版本源码包含对 `ceilf(...)` 的直接调用（第 84 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_simt_hw.h#L84)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
