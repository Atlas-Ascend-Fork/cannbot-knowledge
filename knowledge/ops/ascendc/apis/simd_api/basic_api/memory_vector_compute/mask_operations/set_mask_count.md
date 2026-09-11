---
type: API
title: SetMaskCount
description: 设置Mask模式为Counter模式，直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.masking
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/mask_operations/SetMaskCount.md
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

# SetMaskCount<a name="ZH-CN_TOPIC_0000001790047006"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_common.h"`。

设置Mask模式为Counter模式。该模式下，不需要开发者去感知迭代次数、处理非对齐的尾块等操作，可直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。本接口推荐配合API中isSetMask模板参数使用，当isSetMask为false时，支持用户调用本接口手动管理Counter模式，并通过[SetVectorMask](set_vector_mask.md)设置Counter模式下参与计算的元素个数。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetMaskCount()
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 本接口推荐配合API中IsSetMask模板参数使用，当IsSetMask为false时，支持用户调用本接口手动管理Counter模式并通过[SetVectorMask](set_vector_mask.md)设置Counter模式下参与计算的元素个数。

- 设置为Counter模式的场景，需要在矢量计算使用完之后调用[SetMaskNorm](set_mask_norm.md)将Mask模式恢复为Normal模式，以避免影响后续计算。


- 针对Ascend 950PR/Ascend 950DT，Mask为软仿实现，Tensor前n个数据计算接口内部不会将Mask模式切换为Normal模式。若当前场景已通过本接口设置为Counter模式，接口调用后仍为Counter模式；后续计算需要使用Normal模式时，需手动调用[SetMaskNorm](set_mask_norm.md)进行设置。


## 调用示例<a name="section837496171220"></a>

请参考[Counter模式调用示例](set_vector_mask.md#section837496171220)。


<!-- cannbot:related:start -->
## 相关

- [ResetMask](reset_mask.md)（`related`）：恢复mask值为默认值（全1），表示矢量计算中每次迭代内所有元素都参与运算。；约束：该接口仅在矢量计算API的isSetMask模板参数为false时生效，使用完成后需要使用ResetMask将mask恢复为默认值。。SetMaskCount 进入 Counter 模式后要求调用 ResetMask 恢复全 1 默认掩码，二者构成显式设置与清理的状态生命周期。
- [SetVectorMask](set_vector_mask.md)（`related`）：焦点卡说明 SetVectorMask “支持 Count 模式（按元素计数）和 Norm 模式（按比特位）。”，候选卡用“设置Mask模式为Counter模式，直接传入计算数据量，实际迭代次数由Vector计算单元自动推断。”定义调用前的 Count 模式选择；两者组成状态设置与 mask 数值写入顺序。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Resize 950 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/resize_950.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 201 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_broadcast_nhwc.h#L201)
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 342 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/activation/clipped_swiglu/op_kernel/clipped_swiglu.hpp#L342)
- [FlashAttentionScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 624 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_noquant_block_vec_base.h#L624)
- [DequantSwigluQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dequant_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 417 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dequant_swiglu_quant/op_kernel/dequant_swiglu_quant.h#L417)
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 471 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/flash_attention_score_block_vec_base.h#L471)
- [DynamicQuant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/quant/dynamic_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 127 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/quant/dynamic_quant/op_kernel/dynamic_quant_single_row.h#L127)
- [grouped_matmul_swiglu_quant A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_swiglu_quant.md)（`related`）：算子声明的固定版本源码包含对 `SetMaskCount(...)` 的直接调用（第 406 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_spilit_fusion.h#L406)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
