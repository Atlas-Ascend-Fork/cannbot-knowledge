---
type: API
title: SFA 量化稀疏 token 索引（torch_npu.npu_quant_lightning_indexer）
description: torch_npu.npu_quant_lightning_indexer：使用量化 Q/K 及配套 scale，选出稀疏注意力所需的关键 token 索引。 这是 SFA 的稀疏 token 前处理：接收量化
  query、key 的 INT8 数据和配套 scale，通过内积、尺度恢复、ReLU、weights 加权及 TopK 生成索引。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_lightning_indexer.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:48Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_quant_lightning_indexer
- QuantLightningIndexer
---

# SFA 量化稀疏 token 索引：torch_npu.npu_quant_lightning_indexer

## 用途与语义

使用量化 Q/K 及配套 scale，选出稀疏注意力所需的关键 token 索引。

## 输入、输出与行为

这是 SFA 的稀疏 token 前处理：接收量化 query、key 的 INT8 数据和配套 scale，通过内积、尺度恢复、ReLU、weights 加权及 TopK 生成索引。文档“存8算8”指该索引内积路径，不能据此宣称后续 SparseFlashAttention 全链路也采用 INT8 计算。

## 文档签名

```text
torch_npu.npu_quant_lightning_indexer(query, key, weights, query_dequant_scale, key_dequant_scale, query_quant_mode, key_quant_mode, *, actual_seq_lengths_query=None, actual_seq_lengths_key=None, block_table=None, layout_query='BSND', layout_key='BSND', sparse_count=2048, sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_lightning_indexer.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
