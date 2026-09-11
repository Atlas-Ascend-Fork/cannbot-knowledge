---
type: API
title: SetVectorMask
description: 矢量计算时设置mask，支持Normal模式控制单次迭代参与计算元素和Counter模式控制总计算元素个数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.masking
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetVectorMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_common.h
---

# SetVectorMask<a name="ZH-CN_TOPIC_0000001839731333"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_common.h"`。

本接口用于在矢量计算时设置mask。

- 当模板参数isSetMask = false时，推荐使用本接口。使用前需要先调用[SetMaskCount](set_mask_count.md)/[SetMaskNorm](set_mask_norm.md)手动设置Mask模式，并通过调用本接口设置Counter/Normal模式下的mask。在不同的模式下，mask的含义不同：

    - Normal模式下，mask参数用来控制单次迭代内参与计算的元素个数。此时又可以划分为如下两种模式：
        - 连续模式：表示前面连续的多少个元素参与计算。取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，mask∈\[0, 128\]；当操作数为32位时，mask∈\[0, 64\]；当操作数为64位时，mask∈\[0, 32\]。

        - 逐比特模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。分为maskHigh（高位mask）和maskLow（低位mask）。参数取值范围和操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最大值不同。当操作数为16位时，maskLow、maskHigh∈\[0, 2<sup>64</sup>-1\]，并且不同时为0；当操作数为32位时，maskHigh为0，maskLow∈\[0, 2<sup>64</sup>-1\]；当操作数为64位时，maskHigh为0，maskLow∈\[0, 2<sup>32</sup>-1\]。

    - Counter模式下，mask参数表示整个矢量计算参与计算的元素个数。

- 当模板参数isSetMask = true时，不需要调用本接口，参考[接口内设置Mask](../simd_compute/mask.md#接口内设置mask)。

## 函数原型<a name="section620mcpsimp"></a>

- 适用于Normal模式下mask逐比特模式和Counter模式

    ```cpp
    template <typename T, MaskMode mode = MaskMode::NORMAL>
    __aicore__ static inline void SetVectorMask(const uint64_t maskHigh, const uint64_t maskLow)
    ```

- 适用于Normal模式下Mask连续模式和Counter模式

    ```cpp
    template <typename T, MaskMode mode = MaskMode::NORMAL>
    __aicore__ static inline void SetVectorMask(int32_t len)
    ```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| T | 矢量计算操作数数据类型。 |
| mode | Mask模式，MaskMode类型，定义如下：<br>enum class MaskMode : uint8_t {<br>    NORMAL = 0,  // Normal模式<br>    COUNTER      // Counter模式<br>};|

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| maskHigh | 输入 | Normal模式：对应Normal模式下的逐比特模式，可以按位控制哪些元素参与计算。传入高位mask值。<br>Counter模式：需要置0，本入参不生效。 |
| maskLow | 输入 | Normal模式：对应Normal模式下的逐比特模式，可以按位控制哪些元素参与计算。传入低位mask值。<br>Counter模式：整个矢量计算过程中，参与计算的元素个数。 |
| len | 输入 | Normal模式：对应Normal模式下的Mask连续模式，表示单次迭代内前面连续的多少个元素参与计算。<br>Counter模式：整个矢量计算过程中，参与计算的元素个数。 |

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用[ResetMask](reset_mask.md)将mask恢复为默认值。


- 针对Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品，mask = 0表示指令不会执行计算操作，该接口将被视为NOP（空操作）。


## 调用示例<a name="section837496171220"></a>

可结合[SetMaskCount](set_mask_count.md)与[SetMaskNorm](set_mask_norm.md)使用，先设置Mask模式再设置mask：

- Normal模式调用示例

    ```cpp
    AscendC::LocalTensor<half> dstLocal;
    AscendC::LocalTensor<half> src0Local;
    AscendC::LocalTensor<half> src1Local;
    
    // Normal模式
    AscendC::SetMaskNorm();
    AscendC::SetVectorMask<half, AscendC::MaskMode::NORMAL>(0xffffffffffffffff, 0xffffffffffffffff);  // 逐bit模式
    
    // SetVectorMask<half, MaskMode::NORMAL>(128);  // 连续模式
    // 多次调用矢量计算API,可以统一设置为Normal模式，并设置mask参数，无需在API内部反复设置，省去了在API反复设置的过程，会有一定的性能优势
    // dstBlkStride, src0BlkStride, src1BlkStride = 1,单次迭代内数据连续读取和写入
    // dstRepStride, src0RepStride, src1RepStride = 8,相邻迭代间数据连续读取和写入
    AscendC::Add<half, false>(dstLocal, src0Local, src1Local, AscendC::MASK_PLACEHOLDER, 1, { 1, 1, 1, 8, 8, 8 });
    AscendC::Sub<half, false>(src0Local, dstLocal, src1Local, AscendC::MASK_PLACEHOLDER, 1, { 1, 1, 1, 8, 8, 8 });
    AscendC::Mul<half, false>(src1Local, dstLocal, src0Local, AscendC::MASK_PLACEHOLDER, 1, { 1, 1, 1, 8, 8, 8 });
    AscendC::ResetMask();
    ```

- Counter模式调用示例

    ```cpp
    // Counter模式和tensor高维切分计算接口配合使用
    AscendC::LocalTensor<half> dstLocal;
    AscendC::LocalTensor<half> src0Local;
    AscendC::LocalTensor<half> src1Local;
    int32_t len = 128;  // 参与计算的元素个数
    AscendC::SetMaskCount();
    AscendC::SetVectorMask<half, AscendC::MaskMode::COUNTER>(len);
    AscendC::Add<half, false>(dstLocal, src0Local, src1Local, AscendC::MASK_PLACEHOLDER, 1, { 1, 1, 1, 8, 8, 8 });
    AscendC::Sub<half, false>(src0Local, dstLocal, src1Local, AscendC::MASK_PLACEHOLDER, 1, { 1, 1, 1, 8, 8, 8 });
    AscendC::Mul<half, false>(src1Local, dstLocal, src0Local, AscendC::MASK_PLACEHOLDER, 1, { 1, 1, 1, 8, 8, 8 });
    AscendC::SetMaskNorm();
    AscendC::ResetMask();
    
    // Counter模式和tensor前n个数据计算接口配合使用
    AscendC::LocalTensor<half> dstLocal;
    AscendC::LocalTensor<half> src0Local;
    half num = 2; 
    AscendC::SetMaskCount();
    AscendC::SetVectorMask<half, AscendC::MaskMode::COUNTER>(128); // 参与计算的元素个数为128
    AscendC::Adds<half, false>(dstLocal, src0Local, num, 1);
    AscendC::Muls<half, false>(dstLocal, src0Local, num, 1);
    AscendC::SetMaskNorm();
    AscendC::ResetMask();
    ```

更多示例请参考[接口外设置Mask](../simd_compute/mask.md#接口外设置mask)。


<!-- cannbot:related:start -->
## 相关

- [基于全局掩码复用的计算性能优化](../../../../../guides/operator_practice/simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`explains`）：“在这些场景中，掩码配置保持不变的情况下，遵循“**一次性全局配置，后续复用**”的核心原则：在所有连续计算操作执行之前，通过调用**SetVectorMask**接口完成**全局掩码**的一次性、完整设置mask；随后，所有后续的向量计算接口调用均应将**isSetMask**参数设置为**false**，以明确指示接口跳过内部掩码设置流程，直接**复用已预置**的全局掩码状态。”与“设置 Vector Mask，控制矢量计算接口中参与计算的元素。支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。头文件 `basic_api/kernel_operator_vec_intf.h`。支持 950/a2/a3。”提供双方正文证据。优化指南把 SetVectorMask 用作一次性全局配置并要求后续关闭 isSetMask，API 卡定义其 Count/Norm 掩码合同，指南解释了该 API 的复用用法。
- [ResetMask](reset_mask.md)（`related`）：焦点卡通过“设置 Vector Mask，控制矢量计算接口中参与计算的元素。”改变后续矢量指令状态，候选卡明确“使用完成后需要使用ResetMask将mask恢复为默认值。”；两卡闭合设置后的恢复生命周期，避免 mask 泄漏到后续计算。
- [SetMaskCount](set_mask_count.md)（`related`）：焦点卡说明 SetVectorMask “支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。”，候选卡用“设置Mask模式为Counter模式，直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。”定义调用前的 Count 模式选择；两者组成状态设置与 mask 数值写入顺序。
- [SetMaskNorm](set_mask_norm.md)（`related`）：焦点卡说明 SetVectorMask “支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。”，候选卡规定“设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。”；候选为同一接口选择 Norm 语义并决定 mask 如何解释。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 17 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 202 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nhwc.h#L202)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 343 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L343)
- [BlockSparseAttention A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 121 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/attn_infra/epilogue/block/bsa_block_epilogue_online_softmax.hpp#L121)
- [WeightQuantBatchMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 510 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_custom_nz_splitk.h#L510)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 625 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L625)
- [AddLayerNorm A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_layer_norm.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 214 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_layer_norm/op_kernel/add_layer_norm_base.h#L214)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 472 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_score_block_vec_base.h#L472)
- [DequantSwigluQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 418 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant.h#L418)
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 407 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_spilit_fusion.h#L407)
- [DynamicQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetVectorMask(...)` 的直接调用（第 128 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_quant/op_kernel/dynamic_quant_single_row.h#L128)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
