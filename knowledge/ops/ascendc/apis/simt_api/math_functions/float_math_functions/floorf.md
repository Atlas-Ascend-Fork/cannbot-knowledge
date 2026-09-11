---
type: API
title: Floorf
description: 获取小于或等于输入数据的最大整数值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/floorf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# floorf

## 功能说明

获取小于或等于输入数据的最大整数值。

## 函数原型

```cpp
inline float floorf(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

小于或等于输入数据的最大整数值。特别场景说明如下：

-   当x为nan时，返回值为nan。
-   当x为inf时，返回值为inf。
-   当x为-inf时，返回值为-inf。

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
    __global__ __launch_bounds__(256) void compute_floorf(float *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = floorf(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_floorf_vf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = floorf(x[idx]);
    }

    __global__ __vector__ void run_floorf(__gm__ float *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_floorf_vf>(dim3(256), result, x, count);
    }
    ```

输入输出示例如下：

```
x：0.25, 0.75, 1.25, 1.75
result: 0 0 1 1
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 12 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 82 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_simt_hw.h#L82)
- [UpsampleBicubic2d 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 71 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bicubic_v2/op_kernel/arch35/resize_bicubic_v2_simt_base.h#L71)
- [UpsampleBicubic2dAA 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 73 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa/op_kernel/arch35/upsample_bicubic2d_aa_simt_base.h#L73)
- [UpsampleBicubic2dAAGrad 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 38 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bicubic2d_aa_grad/op_kernel/arch35/upsample_bicubic2d_aa_grad_simt_base.h#L38)
- [UpsampleBilinear2dAA 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 55 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa/op_kernel/arch35/upsample_bilinear2d_aa_simt_base.h#L55)
- [UpsampleBilinear2dAABackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 88 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_bilinear2d_aa_backward/op_kernel/arch35/upsample_bilinear2d_aa_backward_simt_base.h#L88)
- [UpsampleLinear1dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_linear_1d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 53 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_linear_grad/op_kernel/arch35/resize_linear_grad_out1_half.h#L53)
- [UpsampleNearest3d 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_nearest_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 37 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/upsample_nearest3d/op_kernel/arch35/upsample_nearest3d_simt_base.h#L37)
- [UpsampleNearestExact1d 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_nearest_exact_1d_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 109 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_nearest_neighbor_v2/op_kernel/arch35/resize_nearest_neighbor_v2_simt.h#L109)
- [RoiPoolingWithArgMax 950 ACLNN 算子知识](../../../../operators/aclnn/cv/objdetect/roi_pooling_with_arg_max_950.md)（`related`）：算子声明的固定版本源码包含对 `floorf(...)` 的直接调用（第 51 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_pooling_with_arg_max/op_kernel/arch35/roi_pooling_with_arg_max_simt.h#L51)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
