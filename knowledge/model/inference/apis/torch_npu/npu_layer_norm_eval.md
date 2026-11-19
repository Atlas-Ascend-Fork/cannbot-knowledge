---
type: API
title: 推理层归一化（torch_npu.npu_layer_norm_eval）
description: torch_npu.npu_layer_norm_eval：执行推理用 LayerNorm，保持被替换层的归一化轴、权重和 epsilon 语义。 本接口对应 `torch.nn.functional.layer_norm` 的层归一化语义。 保留已有模型的 LayerNorm 调用语义，并记录来源计划废弃及替代方向。
tags:
- task.lookup
- topic.compute.normalization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_layer_norm_eval.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_layer_norm_eval.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/wan/cache/cache_block.py
  role: example
created_at: '2026-11-10T03:38:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_layer_norm_eval
- torch.nn.functional.layer_norm
---


# npu_layer_norm_eval：旧 LayerNorm 入口与迁移边界

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_layer_norm_eval(input, normalized_shape, weight=None, bias=None, eps=1e-05) -> Tensor
```

返回层归一化后的 Tensor，功能对应 torch.nn.functional.layer_norm；normalized_shape 描述待归一化的尾部维度，weight/bias 默认为 None，eps 默认 1e-5。

## 参数与组合限制

固定来源明确标注该接口计划废弃，建议使用 torch.nn.functional.layer_norm。计划废弃不等于已从安装包删除；卡片保留现有调用的解释。不要把函数名中的 eval 推导为自动切换整个模型的训练状态，也不要推导未经声明的 dtype/shape 支持表。

## 验证与模型关联

迁移时使用相同输入、normalized_shape、weight、bias 和 eps 对比输出，再验证图模式与实际软件版本；不能只替换函数名后省略精度核对。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/wan/cache/cache_block.py#L116)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### 推理层归一化：torch_npu.npu_layer_norm_eval

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行推理用 LayerNorm，保持被替换层的归一化轴、权重和 epsilon 语义。

### 输入、输出与行为

本接口对应 `torch.nn.functional.layer_norm` 的层归一化语义。替换时保持归一化轴、weight、bias 和 epsilon 一致，不凭融合或推理名称改变数值契约。

### 文档签名

```text
torch_npu.npu_layer_norm_eval(input, normalized_shape, weight=None, bias=None, eps=1e-05) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_layer_norm_eval.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_layer_norm_eval.md)（primary）
