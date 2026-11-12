---
type: API
title: MoE v2 路由初始化与动态量化（torch_npu.npu_moe_init_routing_v2）
description: torch_npu.npu_moe_init_routing_v2：MoE v2 路由初始化与动态量化。MoE（Mixture of Experts）的routing计算，根据torch_npu.npu_moe_gating_top_k_softmax的计算结果做routing处理，支持不量化和动态量化模式。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:47Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_moe_init_routing_v2
---

# MoE v2 路由初始化与动态量化：torch_npu.npu_moe_init_routing_v2

## 用途与语义

MoE（Mixture of Experts）的routing计算，根据torch_npu.npu_moe_gating_top_k_softmax的计算结果做routing处理，支持不量化和动态量化模式。

## 文档签名

```text
torch_npu.npu_moe_init_routing_v2(x, expert_idx, *, scale=None, offset=None, active_num=-1, expert_capacity=-1, expert_num=-1, drop_pad_mode=0, expert_tokens_num_type=0, expert_tokens_num_flag=False, quant_mode=0, active_expert_range=[], row_idx_type=0) -> (Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

本接口的非量化模式为 `quant_mode=-1`，动态量化为 `quant_mode=1`。该固定版本的签名默认值 `quant_mode=0` 表示静态量化，但参数与约束说明均声明暂不支持，调用时应显式选择支持的模式；不能套用 MC2 dispatch_v2 的 `0/2` 编码。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
