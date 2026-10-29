---
type: Guide
title: LongCat-Lite A2/A3 的 TP、EP 部署与验收流程
description: LongCat-Lite A2/A3 的 TP、EP 部署与验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_tp.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/configuration_longcat_flash_lite.py
created_at: '2026-10-21T09:56:19Z'
updated_at: '2026-10-21T09:56:19Z'
platforms:
- a2
- a3
---

# LongCat-Lite A2/A3 的 TP、EP 部署与验收流程

## 目标、输入与产物

面向固定来源中的 LongCat-Flash-Lite 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/longcat_flash_lite.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 固定减配模型与权重

Lite 的 N-gram 表、MLA 和 zero/identity experts 不等于满配 LongCat-Flash 的部署；不继承 AFD、已撤回 KVP 或满配控核开关。按固定源码区分主词表131072与 EP 报告155136的文档差异，不能用 ngram_vocab_size_ratio 解释为同一个词表。

## 2. 选择固定配置

| 配置 | 路径 | 拓扑 | 场景 |
|---|---|---|---|
| `..._rank_8_8ep.yaml` | EP（[expert-parallel](../../concepts/parallelism/expert_parallel.md)） | attn_tp=4 + attn_dp=2、dense_tp=1(DP)、moe_ep=8、`ngram_embed_tp_size=8`、lmhead_tp=8 | 1K input / 128 output，batch=2 |
| `..._rank_8_8ep_b8.yaml` | 同 EP 拓扑 | 同上，`batch_size=8`（4/DP 组） | 吞吐扩展性 |
| `..._rank_8_8tp.yaml` | TP（[tensor-parallel](../../concepts/parallelism/tensor_parallel.md)） | 全模块 TP=8（MLA/Dense/MoE/Embedding/LM Head） | 单 batch 低时延 |
| `..._rank_8_8tp_4k1k.yaml` | 同 TP=8 | `input_max_len=4096`、`max_new_tokens=1024` | 长输入 |

两路 `exe_mode: "ge_graph"`、BF16、`enable_mla_prolog: true`（默认）。

按实际 YAML 核对 EP 模式的 attn_tp4/attn_dp2、ngram TP8 及主 Embedding部署；纯 TP 为另一条路径。不能把 EP 的 batch 扩展结果当作 TP 路径验收。

## 3. 按平台检查路由与图模式

A2 上来源记录 dispatch_v2 的 experts/rank≤24限制，EP8为32/rank，需核对 enable_moe_mc2_dispatch=false 的回退；A3 不沿用该上限。Prefill double-routing 与 Decode MC2/图模式为不同条件，机制读取 [EP 融合机制](../../concepts/techniques/moe_dispatch_combine_v2.md)。

缓存使用 PA_NZ；Prefill 非 absorb，Decode absorb，不能互换 FA layout。MLA-Prolog 只在 GE 且 q_lora_rank>0 时走融合，可由 enable_mla_prolog=false 关闭；其 token 分歧须独立验收。Ngram buffer、静态 shift、LMHead all_gather_into_tensor 与权重地址固定的图适配由 [既有入图案例](../../optimizations/cases/longcat_lite_ngram_graph_host_gap.md)集中维护。

## 4. 保留文档/源码差异并验收结果

EP 报告的 Prefill RS+AG/SP 描述，在本轮核对的2c45117建模中未见 is_sp/reduce_scatter 对应落地，不将其作为当前开关建议。该组 EP 数据及平台缺口见 [EP 来源草稿](../../optimizations/benchmark_observations/longcat_lite_ep_source_observations.md)；TP 入图结果继续引用既有案例，A3 MLA-Prolog/长输入数据归 [A3 来源观测](../../optimizations/benchmark_observations/longcat_lite_a3_prolog_source_benchmark.md)。首次编译时间与稳态分报。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_tp.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/README.md)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)
- [固定来源 5](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/configuration_longcat_flash_lite.py)
