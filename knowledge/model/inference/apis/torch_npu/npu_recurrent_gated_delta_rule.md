---
type: API
title: 变步长 RGDR 线性注意力（torch_npu.npu_recurrent_gated_delta_rule）
description: torch_npu.npu_recurrent_gated_delta_rule：对线性注意力执行门控递归状态更新与输出计算。 变步长 Recurrent Gated Delta Rule（RGDR），线性注意力的门控递归与状态更新。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_recurrent_gated_delta_rule.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:49Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_recurrent_gated_delta_rule
- RGDR
- Recurrent Gated Delta Rule
---

# 变步长 RGDR 线性注意力：torch_npu.npu_recurrent_gated_delta_rule

## 用途与语义

对线性注意力执行门控递归状态更新与输出计算。

## 输入、输出与行为

变步长 Recurrent Gated Delta Rule（RGDR）用于线性注意力的门控递归。每个时间步消费 q/k/v 和旧状态，更新新状态并计算输出；文档以线性时间复杂度描述其长距离依赖处理机制，这不构成当前模型吞吐或精度的实测保证。

## 文档签名

```text
torch_npu.npu_recurrent_gated_delta_rule(query, key, value, state, *, beta=None, scale=None, actual_seq_lengths=None, ssm_state_indices=None, num_accepted_tokens=None, g=None, gk=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_recurrent_gated_delta_rule.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
