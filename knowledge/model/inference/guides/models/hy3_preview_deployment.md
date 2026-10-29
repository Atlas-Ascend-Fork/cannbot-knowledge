---
type: Guide
title: Hy3-preview A3 部署与路由精度验收流程
description: Hy3-preview A3 部署与路由精度验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/optimization_report.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/models/modeling_hy_v3.py
created_at: '2026-10-21T09:56:18Z'
updated_at: '2026-10-21T10:02:02Z'
platforms:
- a3
---



# Hy3-preview A3 部署与路由精度验收流程

## 目标、输入与产物

面向固定来源中的 Hy3-preview 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/hy3_preview.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 确认模型与环境

使用固定报告的 A3、BF16、16 die（来源明示8卡×2die）路径。报告的 CANN 8.5.0 与 README 的9.0.0不同，记录实际 build。Qwen3-MoE 是机制参考，不能照搬其无 shared expert 的结构；本模型额外有 sigmoid router 和 shared expert。

## 2. 配置 TP/EP、cache 与图模式

固定配置的 Attention/Dense/Embedding/LMHead TP4、MoE EP16，在线切分开启；连续 BSH cache 使用 scatter_update_。Prefill eager，Decode GE；EP 的手工 AllToAll 和 MC2 为不同执行路径。Prefill 可由 moe_chunk_max_len 切分 dispatch/combine 的中间峰值，router top-k 并未同步分块。按 [局部 TP 规则](../../optimizations/rules/local_tp_memory_heavy_projections.md)、[图模式规则](../../optimizations/rules/graph_mode_enable_decision_profiling.md)核对边界。

## 3. 优先检查加载与数学语义

QKV 分离权重必须正确映射到 merged_qkv_proj，避免静默漏载。GMM 使用 transpose view，报告中额外 contiguous 权重副本约35.8GB，会放大编译峰值；这是一项固定实现差异，不外推任何 transpose 都能零拷贝。

Sigmoid 后加 e_score_correction_bias 与融合算子 bias 的位置存在来源已承认的语义差异，须对齐路由选择、权重和任务质量；“输出正常”不能证明等价。MTP layer80 在该实现中跳过加载，不据模型含 MTP 层声称部署启用了投机解码。

## 4. 已回退功能与结果入口

报告在 CANN8.5.0 下因 `super kernel do not support more than 2 real stream` 回退 combine_v2 的 shared_expert_x 参数；不在当前流程重新开启。Multi-stream 保持报告中的关闭状态，若更换形状另按 [多流验收](../../guides/optimization/multi_stream_optimization_workflow.md)判断。图缓存按 [缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)处理。

性能和批次口径集中 [Hy3 A3 来源观测](../../optimizations/benchmark_observations/hy3_a3_source_benchmark.md)；阶段值、最终重编译值与不同 batch 的 Prefill 不混算。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/optimization_report.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/models/modeling_hy_v3.py)
