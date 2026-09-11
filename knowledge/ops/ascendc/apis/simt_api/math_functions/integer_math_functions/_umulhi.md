---
type: API
title: __umulhi
description: 获取输入uint32类型数据x和y乘积的高32位。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.arithmetic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/integer_math_functions/__umulhi.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_functions.h
---

# \_\_umulhi

## 功能说明

获取输入uint32类型数据x和y乘积的高32位。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/zh-cn_formulaimage_0000002531050526.png)

## 函数原型

```cpp
unsigned int __umulhi(unsigned int x, unsigned int y)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数，乘数。 |
| y | 输入 | 源操作数，乘数。 |

## 返回值说明

输入uint32类型数据x和y乘积的高32位。

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
    __global__ __launch_bounds__(1024) void KernelUmulhi(unsigned int* dst, unsigned int* x, unsigned int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __umulhi(x[idx], y[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void KernelUmulhi(__gm__ unsigned int* dst, __gm__ unsigned int* x, __gm__ unsigned int* y)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __umulhi(x[idx], y[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 5 / 5 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Cat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `__umulhi(...)` 的直接调用（第 61 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_simt.h#L61)
- [GatherNd 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/gather_nd_950.md)（`related`）：算子声明的固定版本源码包含对 `__umulhi(...)` 的直接调用（第 66 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/gather_nd/op_kernel/arch35/gather_nd_simt.h#L66)
- [Eye 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/eye_950.md)（`related`）：算子声明的固定版本源码包含对 `__umulhi(...)` 的直接调用（第 86 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/eye/op_kernel/arch35/eye.h#L86)
- [InplaceScatterUpdate 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_scatter_update_950.md)（`related`）：算子声明的固定版本源码包含对 `__umulhi(...)` 的直接调用（第 65 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter/op_kernel/arch35/scatter.h#L65)
- [OneHot 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/one_hot_950.md)（`related`）：算子声明的固定版本源码包含对 `__umulhi(...)` 的直接调用（第 139 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/one_hot/op_kernel/arch35/one_hot.h#L139)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
