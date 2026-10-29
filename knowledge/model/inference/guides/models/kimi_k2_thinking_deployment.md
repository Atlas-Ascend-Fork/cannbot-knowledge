---
type: Guide
title: Kimi-K2-Thinking A3 混合精度部署与验收流程
description: Kimi-K2-Thinking A3 混合精度部署与验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/runner_deepseek.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/models/modeling_deepseek.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/config/kimi_k2_thinking_rank_128_128ep_decode_benchmark.yaml
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/config/kimi_k2_thinking_rank_64_64ep_prefill_benchmark.yaml
created_at: '2026-10-21T09:56:19Z'
updated_at: '2026-10-21T09:56:19Z'
platforms:
- a3
---

# Kimi-K2-Thinking A3 混合精度部署与验收流程

## 目标、输入与产物

面向固定来源中的 Kimi-K2-Thinking 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/kimi_k2_thinking.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 确认独立 legacy 实现

该实践使用 models/kimi-k2-thinking 内的 infer.py、runner_deepseek.py、建模及配置副本，复用 DeepSeek 架构思路，不是直接调用 R1 同一建模文件。MoE W4A16、Attention BF16 分别确认；源未支持 Kimi KV C8，不把 R1 的量化路径套用过来。

## 2. 按阶段选择配置

| 阶段 | 配置文件 | world_size | 并行 | 量化 | 备注 |
| ---- | ------- | ---------- | ---- | ---- | ---- |
| Prefill | `kimi_k2_thinking_rank_64_64ep_prefill_benchmark.yaml` | 64 | **CP64** + moe_ep=64 + dense_tp=1 | MoE W4A16 / Attn BF16 | `enable_multi_streams: True`，`input_max_len: 65536`，`batch_size: 64` |
| Decode | `kimi_k2_thinking_rank_128_128ep_decode_benchmark.yaml` | 128 | **Attn-DP128** + MoE-EP128 + `oproj_tp=8` + `dense_tp=4` + `embed/lmhead_tp=16` | MoE W4A16 / Attn BF16 | `exe_mode: ge_graph`，`next_n: 0`（MTP 代码支持，benchmark 默认不开），`enable_multi_streams: True`，`input_max_len: 65536`，`batch_size: 256` |

> Prefill YAML `cp_size: 64`、`attn_tp_size: 1`、`dense_tp_size: 1`；Decode YAML `cp_size: 128` 字段在 YAML 中保留但 decode 阶段不生效（字段标注 "only active at prefill stage"，代码约定）。

机器/卡数量不能由world_size单独推导，分别核对rank/die拓扑。Prefill CP 条件和通信域复用由 [CP 案例](../../optimizations/cases/deepseek_kimi_a3_prefill_cp.md)维护；Decode Attention DP、MoE EP 与局部投影 TP 的决策读取 [局部 TP 规则](../../optimizations/rules/local_tp_memory_heavy_projections.md)。文档建议的节点区间不是当前任务的默认并行度。

## 3. 检查融合、MTP 与开关差异

MLA-Prolog 的对应源码路径无通用 enable/disable 开关，不能照抄 R1 的 enable_mla_prolog；FIA 的 Flash Decode 与 W4A16 GMM 是不同算子路径。WeightNZ、多流由实际 YAML/实现决定；SuperKernel 未显式写入 benchmark YAML，不再表述为“全部继承即可用”。

MTP 是需要匹配权重的预留能力，benchmark next_n=0；64个 Attention head 不自动证明 MTP收益更好。先按 [MTP 接入](../../guides/integration/mtp_speculative_decode_model_onboarding.md)验收状态与精度，再按 [计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)测量。

## 4. 运行与边界

按固定 README 配置权重、输入、各节点环境并选择对应 infer 入口。小输入与256K长序列使用不同内存预算，不将“支持最大长度”当作任意 batch 都能运行。源文档未提供本页可复用的端到端性能表，不补造收益或接受率。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/kimi-k2-thinking/kimi_k2_thinking_inference_guide.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/runner_deepseek.py)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/models/modeling_deepseek.py)
- [固定来源 5](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/config/kimi_k2_thinking_rank_128_128ep_decode_benchmark.yaml)
- [固定来源 6](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/kimi-k2-thinking/config/kimi_k2_thinking_rank_64_64ep_prefill_benchmark.yaml)
