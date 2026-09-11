---
type: API
title: Sub
description: 根据mask对源操作数srcReg0、srcReg1按元素求差，将结果写入目的操作数dstReg。可选保留进位到carry寄存器。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Sub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h
---

# Sub<a name="ZH-CN_TOPIC_0000001929827652"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径：`"basic_api/reg_compute/kernel_reg_compute_vec_binary_intf.h"`。

该接口根据mask，对源操作数srcReg0、srcReg1进行按元素求差操作，将结果写入目的操作数dstReg。

Carry flag（进位/借位标志）用于表示加法进位或者减法无借位。减法运算在硬件底层通过补码加法实现，该接口可以在carry（MaskReg寄存器）中标记每次补码加法是否产生进位，若srcReg0，~srcReg1，33'b1，按位相加后最高位有进位，在carry中对应位置每4bit设置1，否则写0。

计算结果不保留进位，计算公式如下：

$$
dstReg_i = srcReg0_i - srcReg1_i
$$

计算结果保留进位，计算公式如下：

$$
\{carry_i, dstReg_i\} = \{1'b0, srcReg0_i\} + \{1'b0, \sim srcReg1_i\} + 33'b1
$$

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/reg_sub.png)

输出carry适用场景请参考[SubC功能说明](sub_c.md#功能说明)。

## 函数原型<a name="section620mcpsimp"></a>

-   计算结果不保留进位

    ```cpp
    template <typename T = DefaultType, MaskMergeMode mode = MaskMergeMode::ZEROING, typename U>
    __simd_callee__ inline void Sub(U& dstReg, U& srcReg0, U& srcReg1, MaskReg& mask)
    ```

-   计算结果保留进位

    ```cpp
    template <typename T = DefaultType, typename U>
    __simd_callee__ inline void Sub(MaskReg& carry, U& dstReg, U& srcReg0, U& srcReg1, MaskReg& mask)
    ```

## 参数说明<a name="section622mcpsimp"></a>

**表 1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 操作数数据类型。支持的数据类型请参考[数据类型](#数据类型)。 |
| mode | [MaskMergeMode](../aux_data_types/mask_merge_mode.md)枚举类型，选择MERGING模式或ZEROING模式。<br>&bull; ZEROING模式下，mask未筛选的元素在dstReg中置零。<br>&bull; MERGING模式当前不支持。 |
| U | 源操作数和目的操作数的RegTensor类型，例如RegTensor&lt;half&gt;，由编译器自动推导，用户不需要填写。 |

**表 2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstReg | 输出 | 目的操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| srcReg0 | 输入 | 源操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| srcReg1 | 输入 | 源操作数。<br>类型为[RegTensor](../register_data_types/reg_tensor.md)。 |
| mask | 输入 | 源操作数元素操作的有效指示，详细说明请参考[MaskReg](../register_data_types/mask_reg.md)。 |
| carry | 输出 | 目的操作数。输出进位值。类型为[MaskReg](../register_data_types/mask_reg.md)。 |

## 数据类型

目的操作数与源操作数的数据类型需要保持一致。
- 计算结果不保留进位时，支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。
- 计算结果保留进位时，支持的数据类型为：int32_t、uint32_t。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

- 计算结果不保留进位

    ```cpp
    template<typename T>
    __simd_vf__ inline void SubVF(__ubuf__ T* dstAddr, __ubuf__ T* src0Addr, __ubuf__ T* src1Addr, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
    {
        AscendC::Reg::RegTensor<T> srcReg0;
        AscendC::Reg::RegTensor<T> srcReg1;
        AscendC::Reg::RegTensor<T> dstReg;
        AscendC::Reg::MaskReg mask;
        for (uint16_t i = 0; i < repeatTimes; i++) {
            mask = AscendC::Reg::UpdateMask<T>(count);
            AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);
            AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);
            AscendC::Reg::Sub(dstReg, srcReg0, srcReg1, mask);
            AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
        }
    }
    ```

- 计算结果保留进位

    ```cpp
    template <typename T>
    __simd_vf__ inline void SubVF(__ubuf__ T* dst0Addr, __ubuf__ T* dst1Addr, __ubuf__ T* src0Addr, __ubuf__ T* src1Addr, uint32_t count, uint32_t repeatTimes, uint16_t oneRepeatSize){
        AscendC::Reg::RegTensor<T> srcReg0;
        AscendC::Reg::RegTensor<T> srcReg1;
        AscendC::Reg::RegTensor<T> dstReg0;
        AscendC::Reg::MaskReg mask;
        AscendC::Reg::MaskReg carry = AscendC::Reg::CreateMask<uint8_t>();
        for (uint16_t i = 0; i < repeatTimes; i++) {
            mask = AscendC::Reg::UpdateMask<T>(count);
            AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);
            AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);
            AscendC::Reg::Sub(carry, dstReg0, srcReg0, srcReg1, mask);
            // 8*4B=32B align
            AscendC::Reg::StoreAlign<uint32_t, AscendC::Reg::MaskDist::DIST_NORM>((__ubuf__ uint32_t*)dst1Addr + i * 8, carry);
            AscendC::Reg::StoreAlign(dst0Addr + i * oneRepeatSize, dstReg0, mask);
        }
    }
    ```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 65 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 215 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_nearest_neighbor_v2/op_kernel/arch35/resize_nearest_neighbor_v2_nchw_gather.h#L215)
- [Cat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 429 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/concat/op_kernel/arch35/one_axis_concat_no_align_diff_shape.h#L429)
- [LogSoftmaxBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/log_softmax_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 280 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/log_softmax_grad/op_kernel/arch35/log_softmax_grad_ar_recompute.h#L280)
- [AttentionUpdate 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/attention_update_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 225 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/attention_update/op_kernel/arch35/attention_update_with_lse_regbase.h#L225)
- [ChunkCat 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/chunk_cat_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 265 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/chunk_cat/op_kernel/chunk_cat_arch35.h#L265)
- [SoftmaxCrossEntropyWithLogits 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/softmax_cross_entropy_with_logits_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 419 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/softmax_cross_entropy_with_logits/op_kernel/arch35/softmax_cross_entropy_with_logits_full_load.h#L419)
- [RingAttentionUpdate 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/ring_attention_update_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 98 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/ring_attention_update/op_kernel/arch35/ring_attention_update_regbase_common.h#L98)
- [ReflectionPad2dBackward 950 ACLNN 算子知识](../../../../../operators/aclnn/math/conversion/reflection_pad_2d_backward_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 1405 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/pad_v3_grad/op_kernel/arch35/pad_v3_grad_mirror_gather.h#L1405)
- [SwigluGroupQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/swiglu_group_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 403 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/swiglu_group_quant/op_kernel/arch35/swiglu_group_quant_base.h#L403)
- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `Sub(...)` 的直接调用（第 369 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_swiglu_mx_quant.h#L369)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
