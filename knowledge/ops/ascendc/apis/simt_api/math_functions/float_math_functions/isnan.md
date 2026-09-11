---
type: API
title: Isnan
description: 判断浮点数是否为nan。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.math_function
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/float_math_functions/isnan.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/math_functions.h
---

# isnan

## 功能说明

判断浮点数是否为nan。

## 函数原型

```cpp
inline bool isnan(float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

-   false：输入非nan。
-   true：输入为nan。

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
    __global__ __launch_bounds__(256) void compute_isnan(bool *result, const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = isnan(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(256) inline void compute_isnan_vf(__gm__ bool *result, __gm__ const float *x, uint32_t count)
    {
        const uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= count) {
            return;
        }
        result[idx] = isnan(x[idx]);
    }

    __global__ __vector__ void run_isnan(__gm__ bool *result, __gm__ const float *x, uint32_t count)
    {
        asc_vf_call<compute_isnan_vf>(dim3(256), result, x, count);
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

展示 9 / 9 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [UpsampleTrilinear3d 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_trilinear_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 59 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_upsample_trilinear/op_kernel/arch35/resize_upsample_trilinear_simt_base.h#L59)
- [ForeachMaximumList 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_maximum_list_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 46 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_maximum_list/op_kernel/arch35/foreach_maximum_list_simt.h#L46)
- [GridSampler3D 950 Direct Invoke 算子知识](../../../../operators/direct/cv/image/grid_sampler_3d_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 41 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/grid_sample/op_kernel/arch35/grid_sampler_bilinear_smit_common.h#L41)
- [ForeachMaximumScalar 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_maximum_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 60 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_maximum_scalar/op_kernel/arch35/foreach_maximum_scalar_simt.h#L60)
- [ForeachMaximumScalarList 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_maximum_scalar_list_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_maximum_scalar_list/op_kernel/arch35/foreach_maximum_scalar_list_simt.h#L50)
- [ForeachMinimumList 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_minimum_list_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 46 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_minimum_list/op_kernel/arch35/foreach_minimum_list_simt.h#L46)
- [ForeachMinimumScalar 950 ACLNN 算子知识](../../../../operators/aclnn/nn/foreach/foreach_minimum_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 61 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_minimum_scalar/op_kernel/arch35/foreach_minimum_scalar_simt.h#L61)
- [MaxPool2dWithIndices 950 ACLNN 算子知识](../../../../operators/aclnn/nn/pooling/max_pool2d_with_indices_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 35 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/pooling/max_pool_with_argmax_v3/op_kernel/arch35/max_pool_with_argmax_v3_simt.h#L35)
- [MaxPool3dWithArgmax 950 ACLNN 算子知识](../../../../operators/aclnn/nn/pooling/max_pool3d_with_argmax_950.md)（`related`）：算子声明的固定版本源码包含对 `isnan(...)` 的直接调用（第 42 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/pooling/max_pool3d_with_argmax_v2/op_kernel/arch35/max_pool3d_with_argmax_v2_simt.h#L42)

### 知识正文中的调用示例（部分算子）

展示 1 / 5 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Hardtanh 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/hardtanh_950.md)（`related`）：算子正文包含对 `isnan(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
