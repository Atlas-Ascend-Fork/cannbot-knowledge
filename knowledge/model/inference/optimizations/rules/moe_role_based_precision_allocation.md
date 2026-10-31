---
type: Optimization
title: 大 MoE 量化按模块角色分配精度：路由专家最激进、共享专家 / 注意力保守
description: 大 MoE 量化按模块角色分配精度：路由专家最激进、共享专家 / 注意力保守。大参数量 MoE 部署（EP 并行、长序列 / 大 batch）里，MoE 路由专家权重是单卡显存的大头、属权重搬运 bound。纯 W8A8 已把它压到 int8 但显存仍紧张、限制单卡可容纳的专家数与部署规模时，别再对整模型统一加压或统一保精度——按模块在网络里的角色分配量化精度。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/105
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/464
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/16
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/13
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/114
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:32:47Z'
platforms:
- a3
---

# 大 MoE 量化按模块角色分配精度：路由专家最激进、共享专家 / 注意力保守

## 适用场景

大参数量 MoE 部署（EP 并行、长序列 / 大 batch）里，**MoE 路由专家权重是单卡显存的大头、属权重搬运 bound**。纯 W8A8 已把它压到 int8 但显存仍紧张、限制单卡可容纳的专家数与部署规模时，别再对整模型统一加压或统一保精度——按模块在网络里的**角色**分配量化精度。

## 规则 · 按角色分配精度

把最激进的量化留给「占用最大、最能容忍精度损失」的模块，敏感 / 常开的小项保守：

- **MoE 路由专家（routing experts）的 Linear / GroupedMatmul → 最激进**：降到 W4A8（4bit 权重、8bit 激活）或 W4A16。它们冗余度高、且每 token 只激活一小部分，是量化的主战场。
- **MoE 共享专家（shared experts）的 Linear → 保守**：保持 W8A8（int 路径）/ BF16。共享专家 always-on、更影响精度。
- **注意力 / DenseFFN 的 Linear → 保守**：保持 W8A8 / BF16，注意力尤其精度敏感。

收益动机：W4A8C8 相比 W8A8C8 **仅让 MoE(GroupedMatmul) 部分权重减半**（约省 MoE 权重显存 2x），从而在大 EP 下同一张卡装下更多专家、优化计算访存比、支撑单机部署。规划显存收益时按「GMM 权重减半」估，**不按整模型 2x 估**——只有 GMM 权重减少，其余量化层不变。

## W4 权重必须配 clip 压离群值

W4 权重对离群值（outlier）敏感、量化困难、易掉精度。降路由专家到 W4A8 时**必须启用基于学习的 Clamp（转换脚本的 `--clip`）** 压制离群值，这是守住 W4 精度的前置条件；缺它 W4 易掉精度。配 clip 后仓自报的四项评测（MMLU / GPQA / DROP / MGSM）接近 BF16。

## 与「共享融合算子输入不量化」协同

注意力侧量化哪些 Linear 不是「能省就省」，而是受融合算子数据流约束——同一份 BF16 输入要同时喂 IndexerProlog 与 MLAProlog，故共享 / 前置 Linear 统一不量化。该选层原则见 [dsa-quant-layer-selection](dsa_quant_layer_selection.md)，与本页的 MoE 角色分配叠加成完整的 W8A8C8 → W4A8C8 布局。

## 参考实现及其约束

- W4A8 只纳入 MoE 路由专家（`generate_w4a8_quant` 只把 `mlp.experts` 且 `layer >= first_k_dense_replace` 纳入；converter 的 `group_1` targets `MoEGMM`、`w_num_bits = 4`），共享专家保持 W8A8——参考 cann-recipes-infer 的 [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md) [w4a8c8](../../concepts/quantization/w4a8c8.md)（Atlas A3）与 DeepSeekV4-Pro 的 `w4a8-int` 路径（converter 门控从 `is_fp` 收窄为 `w4a8`）。
- Kimi-K2-Thinking 是模型原生的 MoE W4A16 + Attention BF16 混合精度，本仓做 0day 适配，配套 W4A16 GroupedMatmul 算子在 cann/ops-transformer 开源（外部仓引用、未逐文件核验）。
- 规则可迁移到同族 / 同结构（MoE + shared-expert、DSA）量化；MoEGMM 的 W4 权重打包 / 辅助 bias / scale 编码属该量化算子的转换约定，落静态量化概念页，不在此复制。收益「2x」为 W4 vs W8 位宽的设计披露、精度表为仓自报，均无独立复测。
- 大 EP 装更多专家的前置——为什么优先 W4A8C8 而非 W8A8C8——本页即其判据；C8 KV 侧接线见 [mla-c8-int8-kv-cache-op-wiring](mla_c8_int8_kv_cache_op_wiring.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/105)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/464)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/16)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/13)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/114)（evidence）
