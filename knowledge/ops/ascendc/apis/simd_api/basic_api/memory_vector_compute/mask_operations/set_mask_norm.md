---
type: API
title: SetMaskNorm
description: 设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.masking
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetMaskNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_common.h
---

# SetMaskNorm<a name="ZH-CN_TOPIC_0000001836766205"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_common.h"`。

设置Mask模式为Normal模式。该模式为系统默认模式，支持开发者配置迭代次数。本接口推荐配合API中isSetMask模板参数使用，当isSetMask为false时，支持用户调用本接口手动管理Normal模式，并通过[SetVectorMask](set_vector_mask.md)设置Normal模式下的掩码。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetMaskNorm()
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 本接口推荐配合API中IsSetMask模板参数使用，当isSetMask为false时，支持用户调用本接口手动管理Normal模式并通过[SetVectorMask](set_vector_mask.md)设置Normal模式下的掩码。


- 针对Ascend 950PR/Ascend 950DT，Mask为软仿实现，Tensor前n个数据计算接口内部不会将Mask模式切换为Normal模式。若当前场景已通过[SetMaskCount](set_mask_count.md)设置为Counter模式，接口调用后仍为Counter模式；后续计算需要使用Normal模式时，需手动调用本接口进行设置。


## 调用示例<a name="section837496171220"></a>

请参考[Normal模式调用示例](set_vector_mask.md#section837496171220)。


<!-- cannbot:related:start -->
## 相关

- [ResetMask](reset_mask.md)（`related`）：焦点卡约束“使用完成后需要使用ResetMask将mask恢复为默认值”，候选卡定义“恢复mask值为默认值（全1）”；前者设置 Normal 模式后的清理步骤由后者完成。
- [SetVectorMask](set_vector_mask.md)（`related`）：焦点卡说明 SetVectorMask “支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。”，候选卡规定“设置Mask模式为Normal模式（系统默认），支持开发者配置迭代次数和掩码。”；候选为同一接口选择 Norm 语义并决定 mask 如何解释。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 18 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 216 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nhwc.h#L216)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 350 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L350)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 634 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L634)
- [WeightQuantBatchMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 509 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/weight_quant_batch_matmul_v2/op_kernel/weight_quant_batch_matmul_v2_custom_nz_splitk.h#L509)
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 503 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/flash_attention_score_grad.cpp#L503)
- [AddLayerNorm A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_layer_norm.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 213 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_layer_norm/op_kernel/add_layer_norm_base.h#L213)
- [FlashAttentionScoreGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 214 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch35/flash_attention_score_grad_entry_regbase.h#L214)
- [FastLayerNorm A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/fast_layer_norm.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 158 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/layer_norm_v4/op_kernel/layer_norm_v4_single_read.h#L158)
- [FlashAttentionUnpaddingScoreGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_unpadding_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 503 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/flash_attention_score_grad.cpp#L503)
- [DequantSwigluQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskNorm(...)` 的直接调用（第 427 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant.h#L427)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
