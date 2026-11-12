---
type: API
title: 量化 KV 稀疏注意力（torch_npu.npu_kv_quant_sparse_flash_attention）
description: torch_npu.npu_kv_quant_sparse_flash_attention：`kv_quant_sparse_flash_attention`在`sparse_flash_attention`的基础上支持了[Per-Token-Head-Tile-128量化]输入。
  该版本面向长上下文稀疏注意力，支持量化 KV 的 Per-Token-Head-Tile-128 路径。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_kv_quant_sparse_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:44Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_kv_quant_sparse_flash_attention
---

# 量化 KV 稀疏注意力：torch_npu.npu_kv_quant_sparse_flash_attention

## 用途与语义

`kv_quant_sparse_flash_attention`在`sparse_flash_attention`的基础上支持了[Per-Token-Head-Tile-128量化]输入。

## 输入、输出与行为

该版本面向长上下文稀疏注意力，支持量化 KV 的 Per-Token-Head-Tile-128 路径。稀疏选择减少计算，但离散访存仍可能增加搬运时间；这里不推导通用加速比。

## 文档签名

```text
torch_npu.npu_kv_quant_sparse_flash_attention(query, key, value, sparse_indices, scale_value, key_quant_mode, value_quant_mode, *, key_dequant_scale=None, value_dequant_scale=None, block_table=None, actual_seq_lengths_query=None, actual_seq_lengths_kv=None, sparse_block_size=1, layout_query="BSND", layout_kv="BSND", sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1, attention_mode=0, quant_scale_repo_mode=1, tile_size=128, rope_head_dim=64) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_kv_quant_sparse_flash_attention.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
