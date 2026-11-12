---
type: API
title: GroupNorm 与 SiLU 融合（torch_npu.npu_group_norm_silu）
description: torch_npu.npu_group_norm_silu：融合 GroupNorm 与 SiLU，同时产生归一化统计量及激活结果。 组归一化除激活结果外还提供统计量：文档列出 out、meanOut、rstdOut
  以及 SiLU 输出，其中 rstdOut 为标准差的倒数；消费端必须核对返回项顺序。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_group_norm_silu.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:43Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
aliases:
- torch_npu.npu_group_norm_silu
- GroupNorm SiLU
---

# GroupNorm 与 SiLU 融合：torch_npu.npu_group_norm_silu

## 用途与语义

融合 GroupNorm 与 SiLU，同时产生归一化统计量及激活结果。

## 输入、输出与行为

组归一化除激活结果外还提供统计量：文档列出 out、meanOut、rstdOut 以及 SiLU 输出，其中 rstdOut 为标准差的倒数；消费端必须核对返回项顺序。

## 文档签名

```text
torch_npu.npu_group_norm_silu(input, weight, bias, group, eps=0.00001) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

该文档只明确列出 A2；融合操作的统计输出及 epsilon 等字段需与被替换的 GroupNorm+SiLU 保持一致。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_group_norm_silu.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
