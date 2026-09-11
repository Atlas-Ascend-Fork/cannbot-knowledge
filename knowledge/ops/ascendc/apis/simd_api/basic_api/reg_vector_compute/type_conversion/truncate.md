---
type: API
title: Truncate
description: 将源操作数中的浮点数元素截断为整数值并保留原数据类型，存入目的操作数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.compute.elementwise.type_conversion
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/type_conversion/Truncate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/reg_compute/kernel_reg_compute_vec_vconv_intf.h
---

# Truncate<a name="ZH-CN_TOPIC_0000001929827676"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径：`"basic_api/reg_compute/kernel_reg_compute_vec_vconv_intf.h"`。

将源操作数中的浮点数元素截断为整数值（保留原数据类型），并存入目的操作数。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T = DefaultType, RoundMode roundMode = RoundMode::CAST_NONE, MaskMergeMode mode = MaskMergeMode::ZEROING, typename S>
__simd_callee__ inline void Truncate(S& dstReg, S& srcReg, MaskReg& mask)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数数据类型。支持的数据类型请参考[数据类型](#数据类型)。 |
| roundMode | 舍入模式，取值如下：<br>&bull; RoundMode::CAST_RINT<br>&bull; RoundMode::CAST_ROUND<br>&bull; RoundMode::CAST_FLOOR<br>&bull; RoundMode::CAST_CEIL<br>&bull; RoundMode::CAST_TRUNC |
| mode | [MaskMergeMode](../aux_data_types/mask_merge_mode.md)枚举类型，选择MERGING模式或ZEROING模式。<br>&bull; ZEROING模式下，mask未筛选的元素在dstReg中置零。<br>&bull; MERGING模式当前不支持。 |
| S | srcReg/dstReg类型，例如RegTensor&lt;float&gt;，由编译器自动推导，用户不需要填写。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstReg | 输出 | 目的操作数。 <br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| srcReg | 输入 | 源操作数。 <br>类型为[RegTensor](../register_data_types/reg_tensor.md) |
| mask | 输入 | 源操作数元素操作的有效指示，详细说明请参考[MaskReg](../register_data_types/mask_reg.md)。 |

## 数据类型

目的操作数与源操作数的数据类型需要保持一致。支持的数据类型为：half、bfloat16_t、float。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- float类型只支持不饱和模式。

## 调用示例<a name="section642mcpsimp"></a>

```cpp
template<typename T>
__simd_vf__ inline void TruncVF(__ubuf__ T* dstAddr, __ubuf__ T* srcAddr, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
{
    AscendC::Reg::RegTensor<T> srcReg;
    AscendC::Reg::RegTensor<T> dstReg;
    AscendC::Reg::MaskReg mask;
    for (uint16_t i = 0; i < repeatTimes; i++) {
        AscendC::Reg::LoadAlign(srcReg, srcAddr + i * oneRepeatSize);
        mask = AscendC::Reg::UpdateMask<T>(count);
        AscendC::Reg::Truncate<T, AscendC::RoundMode::CAST_FLOOR, AscendC::Reg::MaskMergeMode::ZEROING>(dstReg, srcReg, mask);
        AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
    }
}
```


<!-- cannbot:related:start -->
## 相关

- [Ceil 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/ceil_950.md)（`related`）：AIV 路线不升精度：FP32、FP16、BF16 均在自身位宽上执行 `MicroAPI::Truncate<T, RoundMode::CAST_CEIL, ZEROING>`；roundMode: 舍入模式，取值如下： • RoundMode::CAST_RINT • RoundMode::CAST_ROUND • RoundMode::CAST_FLOOR • RoundMode::CAST_CEIL • RoundMode::CAST_TRUNC；Ceil 950 的三种 AIV dtype 直接消费 Truncate 的 CAST_CEIL 模式，API 卡可核对 dtype、mask 与舍入合同。
- [Truncate](../../memory_vector_compute/type_conversion/truncate_isasi.md)（`same_topic`）：将源操作数的浮点数元素截断到整数位，保持原数据类型不变，支持多种舍入模式。；将源操作数中的浮点数元素截断为整数值（保留原数据类型），并存入目的操作数。两页定义相同的保留浮点 dtype 的整数化任务，分别覆盖 LocalTensor 多舍入模式与 Reg 形式。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 9 / 9 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AddRmsNormDynamicMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_rms_norm_dynamic_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 658 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_rms_norm_dynamic_mx_quant/op_kernel/arch35/add_rms_norm_dynamic_mx_quant_common.h#L658)
- [RmsNormDynamicMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/rms_norm_dynamic_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 540 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/rms_norm_dynamic_mx_quant/op_kernel/arch35/rms_norm_dynamic_mx_quant_common.h#L540)
- [DynamicBlockMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_block_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 935 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_block_mx_quant/op_kernel/arch35/dynamic_block_mx_quant_base.h#L935)
- [DynamicDualLevelMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_dual_level_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 837 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_dual_level_mx_quant/op_kernel/arch35/dynamic_dual_level_mx_quant_base.h#L837)
- [DynamicMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 896 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_mx_quant/op_kernel/arch35/dynamic_mx_quant_not_tail_axis_optimize_high_perf_large_tail.h#L896)
- [DynamicMxQuantWithDualAxis 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_mx_quant_with_dual_axis_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 1787 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_mx_quant_with_dual_axis/op_kernel/arch35/dynamic_mx_quant_with_dual_axis_base.h#L1787)
- [SwigluBackwardMxQuantWithDualAxis 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/swiglu_backward_mx_quant_with_dual_axis_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 1360 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/swiglu_backward_mx_quant_with_dual_axis/op_kernel/arch35/swiglu_backward_mx_quant_with_dual_axis_regbase.h#L1360)
- [SwigluMxQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/swiglu_mx_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 138 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/swiglu_mx_quant/op_kernel/arch35/swiglu_mx_quant_last_last.h#L138)
- [SwigluMxQuantWithDualAxis 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/swiglu_mx_quant_with_dual_axis_950.md)（`related`）：算子声明的固定版本源码包含对 `Truncate(...)` 的直接调用（第 1389 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/swiglu_mx_quant_with_dual_axis/op_kernel/arch35/swiglu_mx_quant_with_dual_axis_regbase.h#L1389)

### 知识正文中的调用示例

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [InplaceCeil 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/inplace_ceil_950.md)（`related`）：算子正文包含对 `Truncate(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
