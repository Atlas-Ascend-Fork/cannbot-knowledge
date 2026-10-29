---
type: Guide
title: Qwen3-MoE A3 双实现部署与优化验收流程
description: Qwen3-MoE A3 双实现部署与优化验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/qwen3-moe/qwen3_moe_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3_moe/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3_moe/models/modeling_qwen3_moe.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3-moe-sglang/README.md
created_at: '2026-10-21T09:56:20Z'
updated_at: '2026-10-21T09:56:20Z'
platforms:
- a3
---

# Qwen3-MoE A3 双实现部署与优化验收流程

## 目标、输入与产物

面向固定来源中的 Qwen3-MoE 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/qwen3_moe.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 先选自研执行器或 SGLang 路径

models/qwen3_moe 与 models/qwen3-moe-sglang 是独立实践，配置、精度、batch 与计时不能拼接。自研路径按模型和卡数选择实际 YAML；SGLang 路径固定在其 README 声明的框架/patch 组合，不自动适配当前框架版本。

## 2. 自研执行器配置与分支核对

| 配置文件 | world_size | 并行策略 | 备注 |
| ---- | ---- | ---- | ---- |
| `qwen3_235b_16tp.yaml` | 16 | `attn_tp=16`、`moe_tp=16` | 纯 TP 路径，`moe_infer_tp` 走 `npu_swiglu` |
| `qwen3_235b_1tp_16ep.yaml` | 16 | `attn_tp=1`（DP16）、`moe_tp=1`（EP16） | DP Attention + EP MoE |
| `qwen3_235b_128ep.yaml` | 128 | `attn_tp=1`、`moe_tp=1`（EP128） | 大 EP，`ge_graph`，benchmark 主用 |
| `qwen3_235b_attn4tp8dp.yaml` | 32 | `attn_tp=4`（DP8）、`moe_tp=1`（EP32） | 混合 DP/TP Attention，eager 调试 |

> `attn_tp_size` 必须整除 `num_heads`；`num_key_value_heads_per_rank = max(num_key_value_heads // attn_tp_size, 1)` 确保 GQA 场景每卡至少 1 个 KV head。

表中的 world_size 沿原配置单位；不从world_size单独推导A3物理卡数。Attention TP 头整除、QK Norm和行切输出由 [TP 机制](../../concepts/parallelism/tensor_parallel.md)维护。建模实际为 moe_infer_tp、Prefill double-routing、Decode dispatch/combine 三条路径；文档旧名 moe_infer_fusion 不作为真实方法。

## 3. SGLang 按 patch 依赖验收

先核对基础 NPU/量化修改，再检查 forced EPLB、profiler、主模型 GE、MTP1/MTP2 GE、lm_head加载、PD GQA FIA修复与SuperKernel。已有 [Qwen SuperKernel 案例](../../optimizations/cases/qwen3_moe_a3_superkernel_scopes.md)保存分段与整层门控差异，不另复制一套范围规则。MTP按 [接入流程](../../guides/integration/mtp_speculative_decode_model_onboarding.md)验收。

W8A8权重转换中的msmodelslim/drop_offset与自研BF16不可互代；perfect EPLB 仅作性能上界，精度验收关闭。缓存按 [缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)核对 CASE_NAME、后端与形状；不能把一次缓存复用描述成普遍启动收益。

## 4. 结果与边界

两条实践的数字集中 [A3 双实现来源观测](../../optimizations/benchmark_observations/qwen3_moe_a3_source_benchmark.md)；“纯模型时延”不改称端到端在线指标，来源概述阈值不改写成完整实验记录。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/qwen3-moe/qwen3_moe_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3_moe/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3_moe/models/modeling_qwen3_moe.py)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/qwen3-moe-sglang/README.md)
