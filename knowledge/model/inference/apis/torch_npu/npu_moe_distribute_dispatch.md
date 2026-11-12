---
type: API
title: MoE token 派发通信（torch_npu.npu_moe_distribute_dispatch）
description: torch_npu.npu_moe_distribute_dispatch：需与torch\_npu.npu\_moe\_distribute\_combine配套使用，执行MoE的并行部署下的token
  dispatch与combine。 派发按可选量化、EP 的 AlltoAllv、可选 TP AllGatherV 的顺序组织；量化模式、EP/TP 通信域以及返回给 combine 的元数据必须配套。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:46Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_moe_distribute_dispatch
---

# MoE token 派发通信：torch_npu.npu_moe_distribute_dispatch

## 用途与语义

需与torch\_npu.npu\_moe\_distribute\_combine配套使用，执行MoE的并行部署下的token dispatch与combine。

## 输入、输出与行为

派发按可选量化、EP 的 AlltoAllv、可选 TP AllGatherV 的顺序组织；量化模式、EP/TP 通信域以及返回给 combine 的元数据必须配套。

## 文档签名

```text
torch_npu.npu_moe_distribute_dispatch(x, expert_ids, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, scales=None, x_active_mask=None, expert_scales=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, quant_mode=0, global_bs=0, expert_token_nums_type=1) -> (Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
