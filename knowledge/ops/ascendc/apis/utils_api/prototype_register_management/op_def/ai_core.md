---
type: API
title: AICore（OpDef）
description: 设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.implementation.operator_registration
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/AICore.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
---

# AICore<a name="ZH-CN_TOPIC_0000002114097049"></a>

## 功能说明<a name="zh-cn_topic_0000001626208081_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section36583473819"></a>

设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。

## 函数原型<a name="zh-cn_topic_0000001626208081_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section13230182415108"></a>

```
OpAICoreDef &AICore(void)
```

## 参数说明<a name="zh-cn_topic_0000001626208081_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section75395119104"></a>

无

## 返回值说明<a name="zh-cn_topic_0000001626208081_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section25791320141317"></a>

OpAICoreDef请参考[OpAICoreDef](../op_ai_core_def/index.md)。

## 约束说明<a name="zh-cn_topic_0000001626208081_zh-cn_topic_0000001526594958_zh-cn_topic_0000001525424352_section19165124931511"></a>

无



<!-- cannbot:related:start -->
## 相关

- [ACLNN 161001 — ascend910_93 缺算子内核配置](../../../../runbooks/compilation/aclnn_161001_ascend910_93.md)（`exemplifies`）：在 `*_def.cpp` 的 `AICore()` 链上, 为目标设备会上报的**每个** socVersion 显式 `.AddConfig("<soc>")` (参考 hardSwish8 同时 `.AddConfig("ascend910b").AddConfig("ascend910_93")` 的写法)。；设置AICore的配置信息：包括Tiling处理回调函数、能力检查回调函数、基础的配置信息等。。Runbook 的修复在 OpDef 的 AICore 链上为每个设备 socVersion 添加配置，AICore API 卡定义该对象承载基础配置及回调信息，因此 161001 配置缺失是该 API 配置职责的具体故障实例。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例（部分算子）

展示 10 / 31 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleLinear1dBackward 950 ACLNN 算子知识](../../../../operators/aclnn/cv/image/upsample_linear_1d_backward_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [Cat 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/cat_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [InplaceSigmoid A2 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/inplace_sigmoid.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [FlashAttentionVarLenScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_var_len_score_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [ClampMin 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/clamp_min_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [Swish A2 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/swish.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [NsaCompress A2 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/nsa_compress.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [InplaceTril 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/inplace_tril_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [SwishBackward 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/swish_backward_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。
- [MhcPreBackward 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mhc/mhc_pre_backward_950.md)（`related`）：算子正文包含对 `AICore(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
