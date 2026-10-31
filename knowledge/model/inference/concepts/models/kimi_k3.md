---
type: Concept
title: Kimi K3：KDA、Gated MLA、AttnRes 与 LatentMoE
description: 说明 Kimi K3 混合注意力、沿深度聚合的 AttnRes，以及请求级递推状态与 KV Cache 的区别；部署优化另按 950 实践核对。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k3/kimi_k3_inference_guide.md
  role: primary
created_at: '2026-10-29T04:09:03Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- agnostic
---

# Kimi K3：KDA、Gated MLA、AttnRes 与 LatentMoE

## 结构与状态

固定来源描述 93 层 Decoder：前 92 层重复 23 组 KDA–KDA–KDA–Gated MLA，最后一层使用 Gated MLA。首层使用 Dense FFN，其后使用 Stable LatentMoE。模型的原生 1M 上下文能力不表示任意部署都能承载该长度。

KDA 使用带逐 key-channel 衰减的 Delta Rule，维护 ShortConv 的最近输入和每个本地 head 的 128×128 递推矩阵。状态容量不随已处理序列长度线性增长。Gated MLA 保存压缩 KV 历史，缓存容量仍与历史长度有关；两者需要各自的请求归属和状态更新逻辑。

AttnRes 沿网络深度选择历史表示，与沿 token 序列计算的 Attention 不同。Block AttnRes 在块入口预计算历史状态的 Softmax 统计量，随后把当前 partial 通过 Online Softmax 合并；归一化用于打分，加权求和使用原始表示。有限精度下，两阶段计算可能因运算顺序而有细微差异。

Stable LatentMoE 的 routed 分支先从主干宽度降到 latent 空间，完成专家计算后恢复主干宽度，再与 shared 分支相加。Router 的 correction bias 用于选专家，聚合权重使用未加 bias 的 sigmoid 分数归一化。

## 适用边界与验证

上述结构定义不规定某个平台的 TP/EP、通信后端或量化组合。核对模型配置、层型排布、请求与状态行的映射，分别验证 Prefill、Decode 和投机验证后的状态。950 实现的 ReplaySSM 条件见 [Kimi K3 ReplaySSM 状态提交](../../optimizations/rules/kimi_k3_replayssm_state_commit.md)。性能数据见 [950DT 低时延观测](../../optimizations/benchmark_observations/kimi_k3_950dt_low_latency.md)。

## Evidence

结构、三类状态和实现边界来自固定版本 Kimi K3 技术文档。本卡未执行模型推理或精度复测。
