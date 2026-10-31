---
type: Guide
title: GPT-OSS A2 权重准备与 TP 推理验收流程
description: 当前GPT-OSS的sink/滑窗与clamped GLU、packed/Page cache和独立TP组；部署以BF16、batch1/eager示例验收。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/gpt-oss/gpt_oss_optimization.md
  role: supporting
created_at: '2026-10-21T09:56:18Z'
updated_at: '2026-10-29T14:23:20Z'
platforms:
- a2
---

# GPT-OSS A2 权重准备与 TP 推理验收流程

## 目标、输入与产物

面向固定来源中的 GPT-OSS 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/gpt_oss.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

固定 README 的软件边界为 CANN9.0.0、PyTorch2.8.0/torch_npu2.8.0.post4（发布26.0.0）、Python3.11；先按该组合准备环境并记录实际构建，其他组合需另行验证。

## 1. 固定 BF16 权重与输入

固定实践只支持 BF16 权重，原始 MXFP4 不能直接传给样例。按 README 的官方转换入口准备独立 BF16 输出，记录原权重版本；不要将此处“单 device/8 卡”换算成任意模型尺寸。GPT-OSS-20B 用 default prompt；120B 的 LongBench 文本摘要输入与 system prompt 应单独保存。

## 2. 选配置并启动

| 配置文件 | 模型 | world_size | attn_tp / moe_tp / lmhead_tp | exe_mode | dataset |
| ---- | ---- | ---- | ---- | ---- | ---- |
| `gpt_oss_20b.yaml` | GPT-OSS-20B | 1 | 1 / 1 / 1 | eager | default |
| `gpt_oss_120b_8tp.yaml` | GPT-OSS-120B | 8 | 8 / 8 / 8 | eager | LongBench |

> `parallel_config` 要求 `attn_tp_size`、`moe_tp_size`、`lmhead_tp_size` **三者相同**（见 config YAML 注释）。当前示例保持三者相同；源码现在分别注册attn/moe/lmhead组并按各自rank加载、归约，不能再用全局rank替代局部rank。没有EP实现。

当前样例 batch_size=1、eager、仅 TP，在线切分由 `enable_online_split_weight` 控制。修改 model_path 和 infer.sh 对应配置后，从仓库根运行`bash executor/scripts/infer.sh --model gpt_oss --yaml gpt_oss_20b.yaml`等统一入口；不能因 FIA 算子支持图而推导整网已支持图模式、EP 或 MTP。

## 3. 核对模型特有的精度条件

Attention sink 按 head/rank 切分后送入 FIA v2 的 learnable_sink。专家激活为 clamped GLU：gate 上界7、up在[-7,7]、alpha1.702、(up+1)*glu，两个 GMM 都带 bias；不能替换为普通 SwiGLU。当前由get_cache_info声明FullAttention/SlidingWindow的CacheEntry，统一KVCacheManager分配并通过setter绑定；每项声明block_size。packed输入和1D position_ids，Prefill直接计算有效K/V再写cache，Decode先按slot_mapping scatter_nd写入后用相应block_table读PA。旧runner.init_kvcache/连续缓存不是当前路径。

通用 TP 原理见 [TP 机制](../../concepts/parallelism/tensor_parallel.md)，KV 写入见 [KV 写入规则](../../optimizations/rules/paged_kv_cache_write_scatter_update_vs_scatter_nd.md)，FIA 机制见 [FIA](../../concepts/kernels/fused_infer_attention_score.md)。AIV 环境变量按 [AIV/双流边界](../../optimizations/rules/hccl_aiv_expansion_vs_prefill_micro_batch.md)评估，不能承诺在所有输入上加速。

## 4. 结果边界

固定优化文档未提供可复用端到端时延表，本流程不新造 benchmark 或验收阈值。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/README.md)（primary）
- [modeling_gpt_oss.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py)（implementation）
- [gpt_oss_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/gpt-oss/gpt_oss_optimization.md)（supporting）
