---
type: API
title: __bfloat162float
description: 将bfloat16类型数据转换为浮点数，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_bfloat162float

## 功能说明

将bfloat16类型数据转换为浮点数，返回转换后的值。

## 函数原型

```cpp
inline float __bfloat162float(const bfloat16_t x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入转换为浮点数的结果。特别场景说明如下：

| x值 | 返回值 |
|---|---|
| 0 | 0 |
| -0 | -0 |
| nan | nan |
| inf | inf |
| -inf | -inf |

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_bf16.h`头文件。

```cpp
#include "simt_api/asc_bf16.h"
```

## 调用示例

-   SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel__bfloat162float(float* dst, bfloat16_t* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __bfloat162float(x[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__bfloat162float(__gm__ float* dst, __gm__ bfloat16_t* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __bfloat162float(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：将bfloat16类型数据转换为浮点数，返回转换后的值。；float val_f32=__bfloat162float(val)。API 卡定义单值 BF16 到 float 转换，ForeachTan 950 的 BF16 route 直接以该 intrinsic 产生 tanf 的 FP32 输入，构成实现与接口的调用关系。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 14 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 143 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_simt.h#L143)
- [ForeachAcos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_acos_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 66 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_acos/op_kernel/arch35/foreach_acos_simt.h#L66)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 131 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_simt.h#L131)
- [ForeachAddList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_add_list_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 53 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_add_list/op_kernel/arch35/foreach_add_list_simt.h#L53)
- [ForeachAddcdivScalar 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_addcdiv_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 52 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_addcdiv_scalar/op_kernel/arch35/foreach_addcdiv_scalar_simt.h#L52)
- [ForeachAsin 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 48 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_asin/op_kernel/arch35/foreach_asin_simt.h#L48)
- [ForeachAtan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_atan_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 138 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_atan/op_kernel/arch35/foreach_atan_simt.h#L138)
- [ForeachDivList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_div_list_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 110 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_div_list/op_kernel/arch35/foreach_div_list_simt.h#L110)
- [ForeachErfc 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_erfc_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 51 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_erfc/op_kernel/arch35/foreach_erfc_simt.h#L51)
- [ForeachMaximumList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_maximum_list_950.md)（`related`）：算子声明的固定版本源码包含对 `__bfloat162float(...)` 的直接调用（第 74 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_maximum_list/op_kernel/arch35/foreach_maximum_list_simt.h#L74)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
