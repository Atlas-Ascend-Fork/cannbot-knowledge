---
type: API
title: __half2float
description: 将half类型数据转换为浮点数，返回转换后的值。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__half2float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/asc_fp16.h
---

# \_\_half2float

## 功能说明

将half类型数据转换为浮点数，返回转换后的值。

## 函数原型

```cpp
inline float __half2float(const half x)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| x | 输入 | 源操作数。 |

## 返回值说明

输入转换成的浮点数。特殊值如下：

| x值 | 返回值 |
| --- | --- |
| 0 | 0 |
| -0 | -0 |
| nan | nan |
| inf | inf |
| -inf | -inf |

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
    __global__ __launch_bounds__(1024) void kernel__half2float(float* dst, half* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __half2float(x[idx]);
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void kernel__half2float(__gm__ float* dst, __gm__ half* x, uint32_t total_length)
    {
        int idx = threadIdx.x + blockIdx.x * blockDim.x;
        if (idx >= total_length) {
            return;
        }
        dst[idx] = __half2float(x[idx]);
    }
    __global__ __vector__ void cast_kernel(__gm__ float* dst, __gm__ half* x, uint32_t total_length)
    {
        asc_vf_call<kernel__half2float>(dim3(1024), dst, x, total_length);
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [ForeachTan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_tan_950.md)（`related`）：“float val_f32=__half2float(val)”是 FP16 route 进入 tanf 前的实际转换；“功能：将half类型数据转换为浮点数，返回转换后的值。”给出扩精度方向。
- [AscHalf2Float](../../../../simd_api/c_api/reg_compute/reg_convert/asc_half2float.md)（`same_topic`）：将half类型数据转换为float类型，无舍入模式。；功能：将half类型数据转换为浮点数，返回转换后的值。两页定义相同 half 到 float 转换语义，分别提供 Reg C API 与 SIMT 函数形式，便于按编程模型选接口。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 13 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 145 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_circular_simt.h#L145)
- [ForeachAcos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_acos_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 55 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_acos/op_kernel/arch35/foreach_acos_simt.h#L55)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_simt.h#L133)
- [ForeachAddList 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_add_list_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 85 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_add_list/op_kernel/arch35/foreach_add_list_simt.h#L85)
- [ForeachAddcdivScalar 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_addcdiv_scalar_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 42 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_addcdiv_scalar/op_kernel/arch35/foreach_addcdiv_scalar_simt.h#L42)
- [ForeachAsin 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_asin_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 43 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_asin/op_kernel/arch35/foreach_asin_simt.h#L43)
- [ForeachAtan 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_atan_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 105 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_atan/op_kernel/arch35/foreach_atan_simt.h#L105)
- [ForeachCos 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_cos_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 54 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_cos/op_kernel/arch35/foreach_cos_simt.h#L54)
- [ForeachCosh 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_cosh_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 54 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_cosh/op_kernel/arch35/foreach_cosh_simt.h#L54)
- [ForeachErfc 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_erfc_950.md)（`related`）：算子声明的固定版本源码包含对 `__half2float(...)` 的直接调用（第 45 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_erfc/op_kernel/arch35/foreach_erfc_simt.h#L45)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
