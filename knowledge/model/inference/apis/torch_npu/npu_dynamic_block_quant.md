---
type: API
title: 逐块动态量化（torch_npu.npu_dynamic_block_quant）
description: torch_npu.npu_dynamic_block_quant：对输入张量，通过给定的`row_block_size`和`col_block_size`将输入划分成多个数据块，以数据块为基本粒度进行量化。
  按行列块划分输入后，逐块计算 scale 并逐块量化；返回量化结果和每块的 scale。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_block_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:41Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_dynamic_block_quant
---

# 逐块动态量化：torch_npu.npu_dynamic_block_quant

## 用途与语义

对输入张量，通过给定的`row_block_size`和`col_block_size`将输入划分成多个数据块，以数据块为基本粒度进行量化。

## 输入、输出与行为

按行列块划分输入后，逐块计算 scale 并逐块量化；返回量化结果和每块的 scale。不能用全张量共享的单个 scale 代替逐块结果。

## 文档签名

```text
torch_npu.npu_dynamic_block_quant(x, *, min_scale=0.0, round_mode="rint", dst_type=1, row_block_size=1, col_block_size=128) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_block_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
