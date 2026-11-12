---
type: API
title: MoE 专家负载均衡与剪枝（torch_npu.npu_moe_update_expert）
description: torch_npu.npu_moe_update_expert：将逻辑专家映射到实际部署的专家，并按输入 mask 处理专家裁剪。 支持负载均衡和专家剪枝。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_update_expert.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:47Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a3
aliases:
- torch_npu.npu_moe_update_expert
- 专家负载均衡
- 专家剪枝
---

# MoE 专家负载均衡与剪枝：torch_npu.npu_moe_update_expert

## 用途与语义

将逻辑专家映射到实际部署的专家，并按输入 mask 处理专家裁剪。

## 输入、输出与行为

支持负载均衡和专家剪枝。映射后的专家表和 mask 用于 MoE 数据分发及后续处理；逻辑专家、实际部署专家与裁剪标记需要保持一致。

## 文档签名

```text
torch_npu.npu_moe_update_expert(expert_ids, eplb_table, *, expert_scales=None, pruning_threshold=None, active_mask=None, local_rank_id=-1, world_size=-1, balance_mode=0) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_update_expert.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
