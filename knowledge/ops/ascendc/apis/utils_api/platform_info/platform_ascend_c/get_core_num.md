---
type: API
title: GetCoreNum
description: 获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/utils/tiling/platform/platform_ascendc.h
---

# GetCoreNum<a name="ZH-CN_TOPIC_0000002114097973"></a>

## 功能说明<a name="zh-cn_topic_0000001647201621_zh-cn_topic_0000001442758437_section36583473819"></a>

获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。

## 函数原型<a name="zh-cn_topic_0000001647201621_zh-cn_topic_0000001442758437_section13230182415108"></a>

```
uint32_t GetCoreNum(void) const
```

## 参数说明<a name="zh-cn_topic_0000001647201621_zh-cn_topic_0000001442758437_section189014013619"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001647201621_zh-cn_topic_0000001442758437_section25791320141317"></a>


Atlas 训练系列产品，耦合模式，返回AI Core的核数


Atlas 推理系列产品，耦合模式，返回AI Core的核数


Atlas A2 训练系列产品/Atlas A2 推理系列产品，分离模式，返回Vector Core的核数


Atlas A3 训练系列产品/Atlas A3 推理系列产品，分离模式，返回Vector Core的核数


Ascend 950PR/Ascend 950DT，分离模式，返回Vector Core的核数


## 约束说明<a name="zh-cn_topic_0000001647201621_zh-cn_topic_0000001442758437_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001647201621_zh-cn_topic_0000001442758437_section320753512363"></a>

```
ge::graphStatus TilingXXX(gert::TilingContext* context) {
    auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    auto coreNum = ascendcPlatform.GetCoreNum();
    // ... 根据核数自行设计Tiling策略
    context->SetSimdNumBlocks(coreNum);
    return ret;
}
```



<!-- cannbot:related:start -->
## 相关

- [GetCoreNumAic](get_core_num_aic.md)（`related`）：获取当前硬件平台的核数。若AI Core的架构为Cube、Vector分离模式，返回Vector Core的核数；耦合模式返回AI Core的核数。；获取当前硬件平台AI Core中Cube核数。若AI Core的架构为Cube、Vector分离模式，返回Cube Core的核数；耦合模式返回AI Core的核数。。两卡共同处理耦合与 Cube/Vector 分离架构下的核数查询，但通用 GetCoreNum 在分离模式返回 Vector 数，GetCoreNumAic 返回 Cube 数，联合阅读可避免按错执行单元分核。
- [GetCoreNumAiv](get_core_num_aiv.md)（`same_topic`）：获取当前硬件平台的核数。；获取当前硬件平台AI Core中Vector核数。。两卡的产品表给出同一返回合同：分离架构返回 Vector Core 数、耦合架构返回 AI Core 数；它们是围绕同一平台核数查询决策的两个入口说明。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [RopeWithSinCosCache A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/posembedding/rope_with_sin_cos_cache.md)（`related`）：算子正文包含对 `GetCoreNum(...)` 的直接调用；本卡提供该接口契约。
- [RopeWithSinCosCache 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/posembedding/rope_with_sin_cos_cache_950.md)（`related`）：算子正文包含对 `GetCoreNum(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
