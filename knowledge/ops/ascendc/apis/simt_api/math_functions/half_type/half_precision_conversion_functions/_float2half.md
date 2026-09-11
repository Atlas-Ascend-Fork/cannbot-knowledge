---
type: API
title: __float2half
description: 遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__float2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_fp16.h
---

# \_\_float2half

## 功能说明

遵循CAST\_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。

## 函数原型

```cpp
inline half __float2half(const float x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

将float类型数据按照CAST\_RINT模式转换为half类型数据。本接口受全局饱和寄存器的影响，特殊值如下：

| x值 | 非饱和模式返回值 | 饱和模式返回值 |
| --- | --- | --- |
| ±0 | ±0 | ±0 |
| nan | nan | ±0 |
| inf | inf | ASCRT\_MAX\_NORMAL\_FP16 |
| -inf | -inf | -ASCRT\_MAX\_NORMAL\_FP16 |
| x>ASCRT\_MAX\_NORMAL\_FP16 | inf | ASCRT\_MAX\_NORMAL\_FP16 |
| x<-ASCRT\_MAX\_NORMAL\_FP16 | -inf | -ASCRT\_MAX\_NORMAL\_FP16 |

## 约束说明

无

## 需要包含的头文件

使用该接口需要包含`simt_api/asc_fp16.h`头文件。

```cpp
#include "simt_api/asc_fp16.h"
```

## 调用示例

- SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(1024) void kernel__float2half(half* dst, float* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __float2half(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__float2half(__gm__ half* dst, __gm__ float* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __float2half(x[idx]);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“yPtr［idx］=__float2half(result_f32)”是 FP16 route 写回前的实际转换；“功能：遵循CAST_RINT模式，将浮点数转换为半精度浮点数，返回转换后的值。”给出缩精度合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 10 / 10 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ForeachAcos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_acos_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 57 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_acos/op_kernel/arch35/foreach_acos_simt.h#L57)
- [ForeachAddcdivScalar 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_addcdiv_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 47 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_addcdiv_scalar/op_kernel/arch35/foreach_addcdiv_scalar_simt.h#L47)
- [ForeachAsin 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 45 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_asin/op_kernel/arch35/foreach_asin_simt.h#L45)
- [ForeachAtan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_atan_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 107 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_atan/op_kernel/arch35/foreach_atan_simt.h#L107)
- [ForeachCos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_cos_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 69 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_cos/op_kernel/arch35/foreach_cos_simt.h#L69)
- [ForeachCosh 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_cosh_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 69 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_cosh/op_kernel/arch35/foreach_cosh_simt.h#L69)
- [ForeachErfc 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_erfc_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 46 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_erfc/op_kernel/arch35/foreach_erfc_simt.h#L46)
- [ForeachMulList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_mul_list_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 55 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_mul_list/op_kernel/arch35/foreach_mul_list_simt.h#L55)
- [ForeachTanh 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tanh_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 61 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_tanh/op_kernel/arch35/foreach_tanh_simt.h#L61)
- [ForeachAddcdivScalar 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/foreach/foreach_addcdiv_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `__float2half(...)` 的直接调用（第 47 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_addcdiv_scalar/op_kernel/arch35/foreach_addcdiv_scalar_simt.h#L47)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
