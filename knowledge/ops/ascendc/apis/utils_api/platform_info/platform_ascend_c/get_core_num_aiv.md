---
type: API
title: GetCoreNumAiv
description: 获取当前硬件平台AI Core中Vector核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI
  Core的核数。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumAiv.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/utils/tiling/platform/platform_ascendc.h
---

# GetCoreNumAiv<a name="ZH-CN_TOPIC_0000002078498906"></a>

## 功能说明<a name="zh-cn_topic_0000001675101185_zh-cn_topic_0000001442758437_section36583473819"></a>

获取当前硬件平台AI Core中Vector核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。

## 函数原型<a name="zh-cn_topic_0000001675101185_zh-cn_topic_0000001442758437_section13230182415108"></a>

```
uint32_t GetCoreNumAiv(void) const
```

## 参数说明<a name="zh-cn_topic_0000001675101185_zh-cn_topic_0000001442758437_section189014013619"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001675101185_zh-cn_topic_0000001442758437_section25791320141317"></a>


Atlas 训练系列产品，耦合模式，返回AI Core的核数


Atlas 推理系列产品，耦合模式，返回AI Core的核数


Atlas A2 训练系列产品/Atlas A2 推理系列产品，分离模式，返回Vector Core的核数


Atlas A3 训练系列产品/Atlas A3 推理系列产品，分离模式，返回Vector Core的核数


Ascend 950PR/Ascend 950DT，分离模式，返回Vector Core的核数


## 约束说明<a name="zh-cn_topic_0000001675101185_zh-cn_topic_0000001442758437_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001675101185_zh-cn_topic_0000001442758437_section320753512363"></a>

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

- [GetCoreNum](get_core_num.md)（`same_topic`）：获取当前硬件平台的核数。；获取当前硬件平台AI Core中Vector核数。。两卡的产品表给出同一返回合同：分离架构返回 Vector Core 数、耦合架构返回 AI Core 数；它们是围绕同一平台核数查询决策的两个入口说明。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例（部分算子）

展示 10 / 156 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Im2colBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/im2col_backward_950.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [CircularPad2d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [Celu 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/celu_950.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [AttentionToFfn A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/attention_to_ffn.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [Rasterizer A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/rasterizer.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [CircularPad2dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d_backward_950.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [ClippedSwiglu A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/clipped_swiglu.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [DistributeBarrier A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/distribute_barrier.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [ThreeInterpolateBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/three_interpolate_backward.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。
- [CircularPad3d A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_3d.md)（`related`）：算子正文包含对 `GetCoreNumAiv(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
