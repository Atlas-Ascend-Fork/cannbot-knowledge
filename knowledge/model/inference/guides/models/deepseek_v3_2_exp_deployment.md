---
type: Guide
title: DeepSeek-V3.2-Exp A3 长序列部署与验收流程
description: DeepSeek-V3.2-Exp A3 长序列部署与验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek-v3.2-exp/README.md
created_at: '2026-10-21T09:56:17Z'
updated_at: '2026-10-21T09:56:17Z'
platforms:
- a3
---

# DeepSeek-V3.2-Exp A3 长序列部署与验收流程

## 目标、输入与产物

面向固定来源中的 DeepSeek-V3.2-Exp 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/deepseek_v3_2_exp.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 确认实现与精度

区分 AscendC、PyPTO、TileLang 算子实现以及 BF16、W8A8C8、MoE W4A8 + Attention W8A8C8 配置，不因共享 DSA 机制混用 DSL 代码。`indexer.py` 的 PyPTO 分支还受 Decode 与 int8 KVCache 等条件约束。各模块的量化范围保留在下文，质量表统一引用独立观测。

## 2. 按阶段选择配置

| 阶段 | YAML | world_size | 并行 | 量化 | 备注 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Prefill | `deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml` | 64 | CP64 + MoE-EP64 | BF16 | `next_n: 3`、`enable_multi_streams: True` |
| Prefill | `deepseek_v3.2_exp_rank_64_64ep_w8a8c8_prefill_benchmark.yaml` | 64 | CP64 + MoE-EP64 | W8A8C8 | `embed/lmhead_tp_size: 16`（单 node HCCS 内 TP） |
| Decode | `deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml` | 128 | DP128 + MoE-EP128 | BF16 | `oproj_tp_size: 4`、`dense_tp_size: 4` |
| Decode | `deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml` | 128 | DP128 + MoE-EP128 | W8A8C8 | 主 benchmark 配置，`ge_graph` 图模式 |
| Decode | `deepseek_v3.2_exp_rank_128_128ep_w8a8c8_offload_benchmark.yaml` | 128 | DP128 + MoE-EP128 | W8A8C8 | `enable_offload: True` |
| Decode | `deepseek_v3.2_exp_rank_64_64ep_w8a8c8_decode_aclgraph_benchmark.yaml` | 64 | DP64 + MoE-EP64 | W8A8C8 | `acl_graph` 模式 |

> `exe_mode: ge_graph / acl_graph / eager` 三选一（见 [torchair](../../concepts/frameworks/torchair.md)）。`world_size = 2 × chip_num` 在 A3（两 die 一卡）。

Prefill 整域 CP 的数据/通信条件以 [DeepSeek/Kimi CP 案例](../../optimizations/cases/deepseek_kimi_a3_prefill_cp.md)为准；Decode 的投影、Dense、Embedding/LMHead 取 [局部 TP 规则](../../optimizations/rules/local_tp_memory_heavy_projections.md)，通信域与 rank/物理卡单位分别核对。PD 示意中的节点区间是固定来源建议，不能替代当前资源和 SLA 评估。

## 3. 确认量化、MTP 与内存路径

MLAProlog 仅 Q_b_proj W8A8，其余关联输入 Linear 保留高精度；SFA 的 cache Int8 存储、BF16 计算；Indexer Q 与 cache 分别 A8/C8；LI BatchMatmul Int8；路由专家 W8A8/W4A8，共享专家及 O_proj W8A8，LMHead 不量化。C8 的各模块粒度不能相互替换，具体机制见 [W8A8C8](../../concepts/quantization/w8a8c8.md)、[W4A8C8](../../concepts/quantization/w4a8c8.md)。

MTP 的 MLA/LI/SFA 模块分析由 [DSA MTP 案例](../../optimizations/cases/mtp_benefit_sparse_attention_and_latency_metric.md)维护；`next_n=3` 不是收益保证。先按 [MTP 计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)记录接受数与每步/每等效 token 时间，再判断收益。

Offload 路径：Prefill 设备侧复用一层 MLA KV 缓冲并异步写 Host；Decode 由 LI TopK 选择并复用设备已有 cache。接入与容量检查见 [Offload 流程](../../optimizations/rules/kvcache_offload_host_swap.md)；不要把该 MLA 路径推广给任意模型 cache。

## 4. 多流与结果归属

`enable_multi_streams` 控制相关路径，shared/routed expert 与 IndexerProlog 各自有依赖和同步要求，按 [多流验收流程](../../guides/optimization/multi_stream_optimization_workflow.md)检查真实重叠，不因使用了多个 stream 就认定加速。

端到端与容量数据集中 [A3 来源观测](../../optimizations/benchmark_observations/deepseek_v32_a3_source_benchmark.md)；量化精度表归 [量化精度待核验观测](../../optimizations/benchmark_observations/benchmark_deepseek_v32_quant_accuracy.md)，不据此制定其他模型的验收阈值。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek-v3.2-exp/README.md)
