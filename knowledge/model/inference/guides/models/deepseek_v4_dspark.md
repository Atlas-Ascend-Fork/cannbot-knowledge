---
type: Guide
title: DeepSeek-V4 Flash DSpark 部署与拒绝采样验证
description: 基于最新 V4 的 DSpark 配置，核对固定宽度 Verify、拒绝后的缓存位置、A3/950 算子条件与 PD 概率状态传输。
tags:
- task.implementation
- topic.speculative_decoding
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_dspark.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/dspark_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_4_1bs_low_latency_tp_dspark.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_4_4ep_dspark.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pd/prefill.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pd/decode.yaml
  role: implementation
created_at: '2026-10-29T15:20:09Z'
updated_at: '2026-10-29T15:20:09Z'
platforms:
- a3
- '950'
---

# DeepSeek-V4 Flash DSpark 部署与验证

## 输入与准备

使用 Flash DSpark 对应 checkpoint，可将主模型和 proposal 权重放在同一目录，或配置 draft_model_path。确认 inference/config.json 或草稿配置定义正数 n_mtp_layers、严格递增且不重复的 dspark_target_layer_ids，以及有效的 noise token/Markov rank；主模型需收集这些目标层的辅助 hidden。空 draft_model_path 复用主模型目录。

当前支持 A3/950，强制 cp_size=1。A3 依赖支持非空 ori_sparse_indices 和 ori_topk_length 的 SparseFlashMLA/metadata 包；README 前部“仅950”的概述不足以覆盖后面的 A3 配置与实际校验。不要用通用 Worker 的 CP runbook 绕过模型的 CP 检查。

## 选择配置

950 的 ci_950/deepseek_v4_flash_rank_4_4ep_dspark.yaml 使用 world4/batch4、width5；低时延 TP 文件 deepseek_v4_flash_rank_4_1bs_low_latency_tp_dspark.yaml 使用 world4/batch1、width7，attn/o_proj/moe/embed/lmhead TP 均4。A3 PD 的 prefill.yaml/decode.yaml 均 world8/batch8、width5、CP1。按实际卡数和权重调整并保留生效配置，不直接把样例当容量保证。

在 speculative_config 设置 method=dspark 和 num_speculative_tokens；confidence_threshold=0 使用全部 proposal，draft_temperature 为空时沿用请求采样温度。旧 next_n 与显式 width 同时配置时必须匹配。先运行相同权重的无投机基线，再打开 DSpark 检查输出、接受长度、缓存及计时。

## Proposal、Verify 与状态提交

主模型目标层 hidden 进入多个 proposal stage，经块级生成和 Markov/Confidence heads 产生 token 及完整 draft_probs。confidence 只决定每个请求的有效连续前缀；target Verify 仍执行固定 N+1 输入桶，不会因置信度在 rank 间选择不同图。

拒绝采样必须同时拿到 target logits 和 proposal 概率，按请求采样参数还原分布；不能用“逐 token 相等”替代。拒绝后只提交 seed 与接受前缀的 hidden/位置，下一轮 proposal cursor 从已确认位置重建，不能沿用包含被拒绝 token 的物理缓存尾。

主模型与每个 proposal stage 的 KV 内容独立，由框架 SlidingWindow CacheEntry 统一管理请求生命周期；DSpark proposal cache 保持 BF16 PA_BBND，即使主模型使用量化 KV。Attention 读“已确认滑窗上下文 + 完整 Draft Block”的紧凑 PA view，块内为无因果 mask；A3 显式构造稀疏索引和各 query 的有效长度，不能直接套原生 MTP SWA 的因果掩码。

## PD 传输与计时

P/D 需匹配 attention TP、CP1、KV 布局和 speculative codec。传输包括 proposal tokens、effective length 和 FP32 draft_probs；额外概率空间为 N×vocab_size×4 字节/请求，再加 token/长度与对齐，绝非只传几个 token。主/草稿缓存由框架声明，Request 不保存整份 KV 快照。

计时应覆盖实际主模型与 proposal 执行；proposal 的历史 KV 投影/compact gather 在执行窗口内，模型输入和 PA metadata 准备仍在窗口外。区分模型时间、每个输出 token 时间和端到端延时，记录 warmup、采样参数、接受率及输出 token 实际数量。在线带 seed 的复现条件不保证与离线采样逐 token 相同。

本次仅核对源码与配置，没有执行多卡或精度测试。背景见[V4 部署](deepseek_v4_deployment.md)、[投机解码](../../concepts/techniques/mtp_speculative_decoding.md)及[计时诊断](../../runbooks/performance/post_profile_decode_latency.md)。
