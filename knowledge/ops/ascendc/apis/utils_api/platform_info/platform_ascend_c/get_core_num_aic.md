---
type: API
title: GetCoreNumAic
description: 获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI
  Core的核数。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumAic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/utils/tiling/platform/platform_ascendc.h
---

# GetCoreNumAic<a name="ZH-CN_TOPIC_0000002114052977"></a>

## 功能说明<a name="zh-cn_topic_0000001675181281_zh-cn_topic_0000001442758437_section36583473819"></a>

获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。

## 函数原型<a name="zh-cn_topic_0000001675181281_zh-cn_topic_0000001442758437_section13230182415108"></a>

```
uint32_t GetCoreNumAic(void) const
```

## 参数说明<a name="zh-cn_topic_0000001675181281_zh-cn_topic_0000001442758437_section189014013619"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001675181281_zh-cn_topic_0000001442758437_section25791320141317"></a>


Atlas 训练系列产品，耦合模式，返回AI Core的核数


Atlas 推理系列产品，耦合模式，返回AI Core的核数


Atlas A2 训练系列产品/Atlas A2 推理系列产品，分离模式，返回Cube Core的核数


Atlas A3 训练系列产品/Atlas A3 推理系列产品，分离模式，返回Cube Core的核数


Ascend 950PR/Ascend 950DT，分离模式，返回Cube Core的核数


## 约束说明<a name="zh-cn_topic_0000001675181281_zh-cn_topic_0000001442758437_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001675181281_zh-cn_topic_0000001442758437_section320753512363"></a>

```
ge::graphStatus TilingXXX(gert::TilingContext* context) {
    auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    auto aicNum = ascendcPlatform.GetCoreNumAic();
    auto aivNum = ascendcPlatform.GetCoreNumAiv();
    // ...按照aivNum切分
    context->SetSimdNumBlocks(ascendcPlatform.CalcTschNumBlocks(aivNum, aicNum, aivNum));
    return ret;
}
```



<!-- cannbot:related:start -->
## 相关

- [GetCoreNum](get_core_num.md)（`related`）：获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。；获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。。两卡共同处理耦合与 Cube/Vector 分离架构下的核数查询，但通用 GetCoreNum 在分离模式返回 Vector 数，GetCoreNumAic 返回 Cube 数，联合阅读可避免按错执行单元分核。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例（部分算子）

展示 10 / 11 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleBicubic2dAA A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [AddLora A2 ACLNN 算子知识](../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [DeformableConv2d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/conv/deformable_conv2d.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [SparseFlashAttention 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/sparse_flash_attention_950.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [FlatQuant A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/flat_quant.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。
- [AlltoAllAllGatherBatchMatMul A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/allto_all_all_gather_batch_mat_mul.md)（`related`）：算子正文包含对 `GetCoreNumAic(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
