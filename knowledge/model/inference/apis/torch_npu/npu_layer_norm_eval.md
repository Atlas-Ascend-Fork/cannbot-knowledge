---
type: API
title: 推理层归一化（torch_npu.npu_layer_norm_eval）
description: torch_npu.npu_layer_norm_eval：执行推理用 LayerNorm，保持被替换层的归一化轴、权重和 epsilon 语义。 本接口对应 `torch.nn.functional.layer_norm`
  的层归一化语义。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_layer_norm_eval.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:57Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_layer_norm_eval
- torch.nn.functional.layer_norm
---

# 推理层归一化：torch_npu.npu_layer_norm_eval

## 用途与语义

执行推理用 LayerNorm，保持被替换层的归一化轴、权重和 epsilon 语义。

## 输入、输出与行为

本接口对应 `torch.nn.functional.layer_norm` 的层归一化语义。替换时保持归一化轴、weight、bias 和 epsilon 一致，不凭融合或推理名称改变数值契约。

## 文档签名

```text
torch_npu.npu_layer_norm_eval(input, normalized_shape, weight=None, bias=None, eps=1e-05) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_layer_norm_eval.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
