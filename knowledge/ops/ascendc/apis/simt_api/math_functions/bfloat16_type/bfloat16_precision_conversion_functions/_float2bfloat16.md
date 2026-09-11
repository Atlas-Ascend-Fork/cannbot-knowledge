---
type: API
title: __float2bfloat16
description: 遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__float2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_bf16.h
---

# \_\_float2bfloat16

## 功能说明

遵循CAST\_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值。

## 函数原型

```cpp
inline bfloat16_t __float2bfloat16(const float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入遵循CAST\_RINT模式转换成的bfloat16类型数据。本接口受全局饱和模式影响，特殊值如下：

| x值 | 非饱和模式返回值 | 饱和模式返回值 |
|---|---|---|
| 0 | 0 | 0 |
| -0 | -0 | -0 |
| nan | nan | 0 |
| inf | inf | ASCRT_MAX_NORMAL_BF16 |
| -inf | -inf | -ASCRT_MAX_NORMAL_BF16 |
| ＞ASCRT_MAX_NORMAL_BF16 | inf | ASCRT_MAX_NORMAL_BF16 |
| ＜-ASCRT_MAX_NORMAL_BF16 | -inf | -ASCRT_MAX_NORMAL_BF16 |

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
    __global__ __launch_bounds__(1024) void kernel__float2bfloat16(bfloat16_t* dst, float* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __float2bfloat16(x[idx]);
    }
    ```

-   SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__float2bfloat16(__gm__ bfloat16_t* dst, __gm__ float* x)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        dst[idx] = __float2bfloat16(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“yPtr［idx］=__float2bfloat16(result_f32)”是 BF16 route 写回前的实际转换；“遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值。”给出缩精度和舍入合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 8 / 8 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ForeachAcos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_acos_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 68 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_acos/op_kernel/arch35/foreach_acos_simt.h#L68)
- [ForeachAddcdivScalar 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_addcdiv_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_addcdiv_scalar/op_kernel/arch35/foreach_addcdiv_scalar_simt.h#L57)
- [ForeachAsin 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 50 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_asin/op_kernel/arch35/foreach_asin_simt.h#L50)
- [ForeachAtan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_atan_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 140 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_atan/op_kernel/arch35/foreach_atan_simt.h#L140)
- [ForeachErfc 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_erfc_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 52 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_erfc/op_kernel/arch35/foreach_erfc_simt.h#L52)
- [ForeachMulList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_mul_list_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 68 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_mul_list/op_kernel/arch35/foreach_mul_list_simt.h#L68)
- [ForeachTanh 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tanh_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 76 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_tanh/op_kernel/arch35/foreach_tanh_simt.h#L76)
- [ForeachAddcdivScalar 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/foreach/foreach_addcdiv_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2bfloat16(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_addcdiv_scalar/op_kernel/arch35/foreach_addcdiv_scalar_simt.h#L57)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
