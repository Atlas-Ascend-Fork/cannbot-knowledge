---
type: API
title: Duplicate
description: 将标量或源寄存器最低位元素广播到目的寄存器，支持Scalar和Tensor两种模式，可配合mask使用。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_padding/Duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/reg_compute/kernel_reg_compute_vec_duplicate_intf.h
---

# Duplicate<a name="ZH-CN_TOPIC_0000001937477638"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径：`"basic_api/reg_compute/kernel_reg_compute_vec_duplicate_intf.h"`。

支持Scalar和Tensor两种模式：

-   Scalar模式：将scalarValue广播到寄存器，并保存在dstReg中（如果有mask，则保存在dstReg中被mask筛选的位置）。
-   Tensor模式：将srcReg的最低位元素广播到寄存器，并保存在dstReg中被mask筛选的位置。

## 函数原型<a name="section620mcpsimp"></a>

- 将scalarValue广播到寄存器，不支持mask

    ```cpp
    template <typename T = DefaultType, typename U, typename S>
    __simd_callee__ inline void Duplicate(S& dstReg, U scalarValue);
    ```

- 将scalarValue广播到寄存器，支持mask

    ```cpp
    template <typename T = DefaultType, MaskMergeMode mode = MaskMergeMode::ZEROING, typename U, typename S>
    __simd_callee__ inline void Duplicate(S& dstReg, U scalarValue, MaskReg& mask);
    ```

- 将srcReg的最低位元素广播到寄存器

    ```cpp
    template <typename T = DefaultType, HighLowPart pos = HighLowPart::LOWEST, MaskMergeMode mode = MaskMergeMode::ZEROING, typename S>
    __simd_callee__ inline void Duplicate(S& dstReg, S& srcReg, MaskReg& mask)
    ```

## 参数说明<a name="section622mcpsimp"></a>

**表 1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数数据类型。支持的数据类型请参考[数据类型](#数据类型)。 |
| U | scalar的数据类型。支持的数据类型请参考[数据类型](#数据类型)。 |
| mode | [MaskMergeMode](../aux_data_types/mask_merge_mode.md)枚举类型，选择MERGING模式或ZEROING模式。<br>&bull; ZEROING模式下，mask未筛选的元素在dstReg中置零。<br>&bull; MERGING模式下，mask未筛选的元素在dstReg中保留dstReg原值。 |
| pos | 默认为LOWEST，表示将srcReg中的最低位广播至dstReg（暂不支持其他取值）。 |
| S | 目的操作数的RegTensor类型， 例如RegTensor&lt;half&gt;，由编译器自动推导，用户不需要填写。 |

**表 2**  函数参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstReg | 输出 | 目的操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| scalarValue | 输入 | 源操作数。<br>类型为标量。 |
| srcReg | 输入 | 源操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| mask | 输入 | 源操作数中元素有效性的指示，详细说明请参考[MaskReg](../register_data_types/mask_reg.md)。 |

## 数据类型

目的操作数与源操作数的数据类型需要保持一致。支持的数据类型为：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。


## 返回值说明

无

## 约束说明<a name="section177921451558"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

- 示例一

    ```cpp
    template<typename T>
    __simd_vf__ inline void DuplicateVF(__ubuf__ T* dstAddr, T scalarValue, uint16_t oneRepeatSize, uint16_t repeatTimes)
    {
        AscendC::Reg::RegTensor<T> dstReg;
        AscendC::Reg::MaskReg mask = AscendC::Reg::CreateMask<T>();    
        for (uint16_t i = 0; i < repeatTimes; i++) {
            AscendC::Reg::Duplicate(dstReg, scalarValue);
            AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
        }
    }
    ```

- 示例二

    ```cpp
    template<typename T>
    __simd_vf__ inline void DuplicateVF(__ubuf__ T* dstAddr, T scalarValue, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
    {
        AscendC::Reg::RegTensor<T> dstReg;
        AscendC::Reg::MaskReg mask;    
        for (uint16_t i = 0; i < repeatTimes; i++) {
            mask = AscendC::Reg::UpdateMask<T>(count);
            AscendC::Reg::Duplicate(dstReg, scalarValue, mask);
            AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
        }
    }
    ```

- 示例三

    ```cpp
    template<typename T>
    __simd_vf__ inline void DuplicateVF(__ubuf__ T* dstAddr, __ubuf__ T* srcAddr, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
    {
        AscendC::Reg::RegTensor<T> srcReg;
        AscendC::Reg::RegTensor<T> dstReg;
        AscendC::Reg::MaskReg mask;
        for (uint16_t i = 0; i < repeatTimes; i++) {
            mask = AscendC::Reg::UpdateMask<T>(count);
            AscendC::Reg::LoadAlign(srcReg, srcAddr + i * oneRepeatSize);
            AscendC::Reg::Duplicate(dstReg, srcReg, mask);
            AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
        }
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：“安装头文件的真实声明表明，寄存器到寄存器重载的模板形参依次是 `T, HighLowPart pos, MaskMergeMode mode`。”给出实际编译修复，而“参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: scalar的数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式下，mask未筛选的元素在dstReg中保留dstReg原值。；pos: 默认为LOWEST，表示将srcReg中的最低位广播至dstReg（暂不支持其他取值）。；S: 目的操作数的RegTensor类型， 例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；srcReg(输入): 源操作数。 类型为RegTensor。”定义 Duplicate 的 pos/mode 契约；runbook 直接示范模板顺序错误及正确实例化。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：焦点卡验证“去掉 RegTensor→Duplicate 直连，并改为 `StoreAlign` 到 32B UB 标量槽、`GetValue(0)` 读回 C++ 标量、再调用标量 `Duplicate` 后，两个末轴 fp32 探针同时恢复。”，候选 API 明确“Scalar模式：将scalarValue广播到寄存器，并保存在dstReg中（如果有mask，则保存在dstReg中被mask筛选的位置）。”；修复正是强制选用这一 Scalar 广播合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 111 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 176 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nchw.h#L176)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 426 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_no_align_diff_shape.h#L426)
- [ClippedSwiglu 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 59 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/arch35/clipped_swiglu_kernel.h#L59)
- [AttentionUpdate 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/attention_update_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 220 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/arch35/attention_update_with_lse_regbase.h#L220)
- [ChunkCat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 232 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat_arch35.h#L232)
- [GeluQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/gelu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 306 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/gelu_quant/op_kernel/arch35/gelu_dynamic_quant_regbase.h#L306)
- [FusedCausalConv1d 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/fused_causal_conv1d_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 60 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/fused_causal_conv1d/op_kernel/arch35/vf/fused_causal_conv1d_no_state_double_tail.h#L60)
- [InplaceClampMax 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/inplace_clamp_max_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 965 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/cast/op_kernel/arch35/cast_impl.h#L965)
- [SoftmaxCrossEntropyWithLogits 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/softmax_cross_entropy_with_logits_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 352 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/softmax_cross_entropy_with_logits/op_kernel/arch35/softmax_cross_entropy_with_logits_full_load.h#L352)
- [InplaceFusedCausalConv1d 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/inplace_fused_causal_conv1d_950.md)（`related`）：算子声明的固定版本源码包含对 `Duplicate(...)` 的直接调用（第 60 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/fused_causal_conv1d/op_kernel/arch35/vf/fused_causal_conv1d_no_state_double_tail.h#L60)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
