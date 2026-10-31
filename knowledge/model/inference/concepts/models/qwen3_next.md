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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T12:00:02Z'
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
