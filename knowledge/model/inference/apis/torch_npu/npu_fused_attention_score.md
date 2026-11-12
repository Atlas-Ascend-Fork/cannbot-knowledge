---
type: API
title: 旧版注意力融合（torch_npu.npu_fused_attention_score）
description: torch_npu.npu_fused_attention_score：旧版 Transformer attention score 融合接口，使用前须确认其版本与产品范围。 旧版 Transformer
  Attention Score 融合链包含 matmul、transpose、add、softmax、dropout、batchmatmul、permute；不能与推理用 FIA 仅凭名称混同。
tags:
- task.lookup
- topic.model_serving
status: draft
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_fused_attention_score.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:56Z'
updated_at: '2026-11-10T11:59:36Z'
platforms: []
aliases:
- torch_npu.npu_fused_attention_score
---

# 旧版注意力融合：torch_npu.npu_fused_attention_score

## 用途与语义

旧版 Transformer attention score 融合接口，使用前须确认其版本与产品范围。

## 输入、输出与行为

旧版 Transformer Attention Score 融合链包含 matmul、transpose、add、softmax、dropout、batchmatmul、permute；不能与推理用 FIA 仅凭名称混同。

## 文档签名

```text
torch_npu.npu_fused_attention_score(query_layer, key_layer, value_layer, attention_mask, scale, keep_prob, query_transpose=False, key_transpose=False, bmm_score_transpose_a=False, bmm_score_transpose_b=False, value_transpose=False, dx_transpose=False) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

该文档只使用旧的 Atlas 训练/推理产品名称，尚未定位到本仓 A2/A3/950 等规范产品范围；保留 draft 与空平台。可在未定位 API 查询中读取定义，不能作为目标平台已支持的证据。

源表分组：Beta。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_fused_attention_score.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
