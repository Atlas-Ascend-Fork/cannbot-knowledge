---
type: Guide
title: HSTU A2 推荐推理接入、缓存与并行验收流程
description: HSTU A2 推荐推理接入、缓存与并行验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hstu/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/hstu_optimization.md
  role: primary
created_at: '2026-10-21T09:56:18Z'
updated_at: '2026-10-29T14:19:33Z'
platforms:
- a2
---

# HSTU A2 推荐推理接入、缓存与并行验收流程

## 目标、输入与产物

面向固定来源中的 HSTU 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/hstu.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 固定依赖与数据准备

按固定 README 核对 RecSDK-Torch、CANN、nnal、recsys-examples v25.11 及 hstu_cann.patch；CATLASS_HOME、torchrec/fbgemm_npu 路径取实际安装值，不把列出的包版本当作已跑通的本机环境。先准备 kuairand-1k 推理数据与 gin 配置，再检查 jagged offsets 和候选物品数量。

## 2. 核对 NPU 适配与 cache 布局

NPU kv_cache_manager_impl 替代原 tensorrt-llm 管理，涵盖池分配、序列加入/淘汰、cached position/token 和 block IDs；dynamic embedding 用 nn.Embedding。`hstu_paged` 处理 jagged、候选物品和 paged KV，不能按标准 LLM Softmax FA 替换。`silu_scale=1/max_seq_len`、历史/候选 offsets、page metadata 必须属于同一请求。

KV 布局由 [pages,layers,2,block] 调为 [layers,2,pages,block]，append 走 `_npu_reshape_and_cache`。concat_nd_jagged 是基于 RecSDK concat_2d_jagged 的 n≥2 输入扩展；in_linear_silu 为另一融合入口。算子接口细节回到固定 README/实现，不在流程中重复完整参数表。

## 3. 启动与并行选择

以下相对路径命令在固定源码的 `models/hstu/` 目录下执行，先按README准备依赖与数据。

- 入口脚本：`models/hstu/inference/inference_gr_ranking.py`
- gin config：`models/hstu/inference/configs/kuairand_1k_inference_ranking.gin`
- 推理模式：
 - **eval 模式**：`--mode eval --enable_fused_ops all`
 - **simulate 模式**：`--mode simulate --enable_fused_ops all`
 - **profiling**：追加 `--enable_profiler`
- 数据集：`kuairand-1k`（`python3 ./preprocessor.py --dataset_name "kuairand-1k" --inference` 预处理）

单机两卡分布式推理示例：

```bash
ASCEND_RT_VISIBLE_DEVICES=0,1 \
torchrun --rdzv-backend=c10d --rdzv-endpoint=localhost:6000 \
 --nnodes=1 --nproc-per-node=2 \
 ./inference/inference_gr_ranking.py \
 --gin_config_file ./inference/configs/kuairand_1k_inference_ranking.gin \
 --embed_tp_size 2 --mode eval --enable_fused_ops all
```

Embedding 侧先按 [大表切分规则](../../optimizations/rules/generative_recommender_vocab_parallel_embedding.md)判断切分对象和小表门控，再验证 DP→TP→DP 通信；不把 dense TP 作为推荐模型的默认解。KV offload 在每层 Attention 后异步触发的机制见 [HSTU Offload 变体](../../concepts/techniques/kvcache_offload.md)，在 eager/ACLGraph 下分别检查生命周期与重叠。

## 4. 验证输出和来源边界

分别检查 eval、simulate、profiling 的输入和指标，确认数据预处理、cache append、eviction 和多卡输出一致。优化文档同时把部分 offload/前处理列为 TODO，不能将计划视作所有分支均已覆盖。原总览引述的论文业务 A/B 数字没有本实践的对应实验，不作为本 NPU 适配收益或验收值。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hstu/README.md)（primary）
- [hstu_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hstu/hstu_optimization.md)（primary）
