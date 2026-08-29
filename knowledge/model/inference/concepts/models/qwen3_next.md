---
type: Concept
title: Qwen3-Next
description: Qwen3-Next 是交替使用 Gated Attention 与 Gated DeltaNet、并结合 MoE FFN 的混合注意力模型；模型结构与具体昇腾部署参数分开治理。
tags:
- task.design
- task.lookup
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/qwen3-next/qwen3_next_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- agnostic
---

# Qwen3-Next

## 模型结构

Qwen3-Next 以 `Qwen3-Next-80B-A3B-Instruct` 为代表规格，总参数约 80B、每个 token 激活参数约 3B。Transformer Block 交替使用 Gated Attention 与 Gated DeltaNet（GDN），并配合 shared 与 routed experts 组成的 MoE FFN。

- **Gated Attention** 使用 Softmax Attention 处理需要精确长程检索的层，计算量随序列长度平方增长。
- **Gated DeltaNet** 使用 Conv1d 和递推状态进行线性复杂度上下文聚合，维护 `conv_state` 与 `ssm_state`。
- **MoE FFN** 只激活部分 routed experts，并可包含 shared expert；具体并行与通信策略由部署实现决定。

## 状态与并行边界

GDN 沿序列方向执行卷积并维护递推状态，因此不能仅根据普通 Attention 的 head 切分方式推导其 Sequence Parallel 行为。MTP 等一次验证多个 token 的路径还必须根据接收结果选择性回写 GDN 状态，避免下一轮读取未被接受 token 的状态。

这些是模型结构带来的约束，不等价于某个平台上的推荐并行度、融合 Kernel 或启动参数。Atlas A3 的 CP/TP/EP、MTP、量化和图模式实践单独维护在 [Qwen3-Next Atlas A3 推理部署与优化指南](../../guides/models/qwen3_next_atlas_a3_deployment.md)。

## 验证方式

- 从模型实现或固定版本说明确认层序中 Gated Attention、GDN 与 MoE 的组合。
- 检查 GDN 的 Conv1d、`conv_state` 和 `ssm_state` 更新是否与推理阶段一致。
- 平台部署结论必须继续核对相应平台 Guide，不能由本 Concept 的 `agnostic` 范围外推。

## 相关知识

- [Gated Attention](../modules/gated_attention.md)
- [Gated DeltaNet](../modules/gated_deltanet.md)
- [MTP Speculative Decoding](../techniques/mtp_speculative_decoding.md)
- [Qwen3.5-MoE](qwen3_5_moe.md)
- [Qwen3-MoE](qwen3_moe.md)

<!-- cannbot:related:start -->
## 相关

- [Qwen3-Next Atlas A3 推理部署与优化指南](../../guides/models/qwen3_next_atlas_a3_deployment.md)（`related`）：Qwen3-Next 的 Transformer Block 中按层交替使用 ［gated-attention］(../../concepts/modules/gated_attention.md) 与 ［gated-deltanet］(../../concepts/modules/gated_deltanet.md)，配合 MoE FFN（shared + routed experts）构成混合注意力 + MoE 架构。；Qwen3-Next 以 `Qwen3-Next-80B-A3B-Instruct` 为代表规格，总参数约 80B、每个 token 激活参数约 3B。Transformer Block 交替使用 Gated Attention 与 Gated DeltaNet（GDN），并配合 shared 与 routed experts 组成的 MoE FFN。。指南以概念卡定义的交替 Attention/GDN 与 MoE 结构为基础，继续给出 Atlas A3 的 TP、CP、EP、融合 Kernel 和量化部署选择。
- [Qwen3.5-MoE](qwen3_5_moe.md)（`related`）：“Qwen3.5-MoE 是 Qwen3.5 系列中的混合专家模型，结构上**同时包含 full attention、linear attention（Gated DeltaNet）和 MoE 三类 block**，是 ［qwen3-next］(qwen3_next.md) 混合注意力思路的延续与放大。”；“Qwen3-Next 以 `Qwen3-Next-80B-A3B-Instruct` 为代表规格，总参数约 80B、每个 token 激活参数约 3B。Transformer Block 交替使用 Gated Attention 与 Gated DeltaNet（GDN），并配合 shared 与 routed experts 组成的 MoE FFN。”。前者明确把自身架构定义为后者混合注意力思路的延续，后者给出被延续的 Gated Attention、GDN 与 shared/routed MoE 组合。
- [recurrent_gated_delta_rule](../kernels/recurrent_gated_delta_rule.md)（`related`）：- 位置：Qwen3-Next 每层 GDN 的 Decode 路径末端，替换原 `fused_recurrent_gated_delta_rule_update` Triton/Python 实现。；MTP 等一次验证多个 token 的路径还必须根据接收结果选择性回写 GDN 状态，避免下一轮读取未被接受 token 的状态。。模型卡给出 MTP 选择性回写 GDN 状态的正确性约束，kernel 卡定位到 Qwen3-Next decode 末端并实现该状态更新。
<!-- cannbot:related:end -->
