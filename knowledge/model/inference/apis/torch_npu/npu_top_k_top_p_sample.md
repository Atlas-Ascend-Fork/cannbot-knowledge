---
type: API
title: TopK TopP 过滤与指数采样（torch_npu.npu_top_k_top_p_sample）
description: torch_npu.npu_top_k_top_p_sample：按 logits、top-k/top-p 和随机权重进行候选筛选及采样，并返回所选索引和相关分布。 输出 `logits_select_idx`
  为所选位置，`logits_top_kp_select` 为 top-k/top-p 处理后的分布。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_top_k_top_p_sample.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_top_k_top_p_sample
- topK-topP-Sample
---

# TopK TopP 过滤与指数采样：torch_npu.npu_top_k_top_p_sample

## 用途与语义

按 logits、top-k/top-p 和随机权重进行候选筛选及采样，并返回所选索引和相关分布。

## 输入、输出与行为

输出 `logits_select_idx` 为所选位置，`logits_top_kp_select` 为 top-k/top-p 处理后的分布。topK、topP、指数采样可分别使能；仅走 Softmax-Argmax 路径时按最大值选择，不能把含随机权重 q 的所有采样路径都等同于 argmax。

## 文档签名

```text
torch_npu.npu_top_k_top_p_sample(logits, top_k, top_p, q=None, eps=1e-8, is_need_logits=False, top_k_guess=32) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_top_k_top_p_sample.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
