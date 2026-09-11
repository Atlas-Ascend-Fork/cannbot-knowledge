---
type: API
title: ResetMask
description: 恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.masking
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/ResetMask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
source_headers:
- include/basic_api/kernel_common.h
---

# ResetMask<a name="ZH-CN_TOPIC_0000001857638449"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为:`"basic_api/kernel_common.h"`。

恢复mask的值为默认值（全1），表示矢量计算中每次迭代内的所有元素都将参与运算。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void ResetMask()
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

调用SetVectorMask接口之后，如需恢复mask的值为默认值（全1），可调用本接口实现。

## 调用示例<a name="section837496171220"></a>

用[SetVectorMask](set_vector_mask.md)设置mask值并使用完成后，使用ResetMask恢复mask的值为默认值。

```cpp
AscendC::SetVectorMask<half, AscendC::MaskMode::NORMAL>(128);
AscendC::ResetMask();
```

更多示例请参考[接口外设置Mask](../simd_compute/mask.md#接口外设置mask)。


<!-- cannbot:related:start -->
## 相关

- [Ors](../logical_compute/ors.md)（`related`）：约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。；恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。。Ors 的手工 mask 路径明确要求结束后调用 ResetMask，后者定义恢复后的全 1 状态。
- [SetMaskCount](set_mask_count.md)（`related`）：恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。；约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。。SetMaskCount 进入 Counter 模式后要求调用 ResetMask 恢复全 1 默认掩码，二者构成显式设置与清理的状态生命周期。
- [SetMaskNorm](set_mask_norm.md)（`related`）：焦点卡约束“使用完成后需要使用ResetMask将mask恢复为默认值”，候选卡定义“恢复mask值为默认值（全1）”；前者设置 Normal 模式后的清理步骤由后者完成。
- [SetVectorMask](set_vector_mask.md)（`related`）：焦点卡通过“设置 Vector Mask，控制矢量计算接口中参与计算的元素。”改变后续矢量指令状态，候选卡明确“使用完成后需要使用ResetMask将mask恢复为默认值。”；两卡闭合设置后的恢复生命周期，避免 mask 泄漏到后续计算。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 12 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 217 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nhwc.h#L217)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 351 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L351)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 635 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L635)
- [WeightQuantBatchMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 591 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_custom_nz_splitk.h#L591)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 482 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_score_block_vec_base.h#L482)
- [AddLayerNorm A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_layer_norm.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 110 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_layer_norm/op_kernel/add_layer_norm_base.h#L110)
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 411 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_spilit_fusion.h#L411)
- [DequantSwigluQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 428 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant.h#L428)
- [MoeTokenPermute A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/moe/moe_token_permute.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 61 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_token_permute/op_kernel/moe_sort_base.h#L61)
- [DynamicQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_quant.md)（`related`）：算子声明的固定版本源码包含对 `ResetMask(...)` 的直接调用（第 133 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_quant/op_kernel/dynamic_quant_single_row.h#L133)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
