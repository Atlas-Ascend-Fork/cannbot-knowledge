---
type: Guide
title: HunyuanVideo 分版本的并行、稀疏与量化验收流程
description: HunyuanVideo 分版本的并行、稀疏与量化验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/hunyuan_video_optimization.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/sample_video.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/models/hunyuan-video/sample_video.py
created_at: '2026-10-21T09:56:21Z'
updated_at: '2026-10-22T01:47:21Z'
platforms:
- a2
- a3
- '950'
---
# HunyuanVideo 分版本的并行、稀疏与量化验收流程

## 目标、输入与产物

面向固定来源中的 HunyuanVideo 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/hunyuan_video.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 固定完整生成任务

保存权重、prompt/negative prompt、seed、分辨率、帧数、采样步、VAE设置与实际配置。统一infer.sh把缓存通过 --cache-config 传入，single/sp8与single_fp8/single_sparse/sp8_sparse不是同一个实验分支，入口机制见 [多模态启动](../../concepts/frameworks/mm_inference_launch.md)。

## 2. 从已有入口选择组合

| 任务 | 规范入口和本模型差异 |
| --- | --- |
| 融合Attention/Norm/RoPE | [DiT迁移规则](../../optimizations/rules/cuda_native_dit_video_attention_sp_npu_adaptation.md)；cu_seqlens有值时分段FA再拼接，RoPE采用interleave，不将源码短例当完整参数契约 |
| Ulysses/Ring/VAE | [SP规则](../../optimizations/rules/video_dit_ulysses_sequence_parallel.md)、[Ring overlap流程](../../optimizations/rules/ring_attention_comm_compute_overlap_lse_merge.md)、[VAE流程](../../optimizations/rules/vae_multicard_spatial_parallel.md) |
| DiT cache | [cache与SP规则](../../optimizations/rules/dit_cache_with_sequence_parallel.md)；分布式l1_loss同步，质量另验；mask缓存与VAE offload独立测量 |
| 950量化 | [950接入案例](../../optimizations/cases/hunyuan_video_950_fp8_quantization.md)与[量化规则](../../optimizations/rules/video_dit_fp8_mxfp8_quantization.md)；量化FA仅Ulysses，不由稀疏Ring支持推导量化FA也支持Ring |

## 3. 不混用两个固定版本的稀疏条件

2c45117 的 sample_video.py 对 sparse+ring_degree>1明确报错；TopK拥有head负载重排接口，SVG在hasattr守卫下跳过。46485bef的同文件已移除该守卫，对应文档另描述Ring TopK/SVG及LSE overlap；其文档还要求匹配稀疏算子实现。两个版本分别验收，不把后版文档的Ring配置套到前版。

稀疏和cache都会改写block forward，按对应版本的互斥条件执行。TopK的本地q/全局KV、首帧dense回填与LSE合并流程，只按该版本实现验证。通用机制见 [块稀疏Attention](../../concepts/modules/blockwise_sparse_attention.md)。

## 4. 结果归属与质量边界

A3累计数据归 [A3观测](../../optimizations/benchmark_observations/hunyuan_video_a3_source_benchmark.md)，950PR量化表归 [950观测](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)；稀疏表缺少逐表硬件/实验记录，保留在 [稀疏来源草稿](../../optimizations/benchmark_observations/hunyuan_video_sparse_source_observations.md)。不沿用旧总览“假定所有表都是5s720p129帧”的口径，也不把跳步缓存“画质良好”的作者判断当验收。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/hunyuan_video_optimization.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/hunyuan-video/hunyuan_video_optimization.md)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/README.md)
- [固定来源 5](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/sample_video.py)
- [固定来源 6](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/models/hunyuan-video/sample_video.py)

## 历史 2c45117 稀疏集成补充

以下为旧入口的配置与外部算子准备说明，仅按对应提交复核；不与后续 Ring 能力混用，也不代表本仓已执行安装/编译。模型专用参数应以固定配置文件为准。


### 历史配置

- **适用载荷**：DiT 超长序列 Attention（固定来源的 HunyuanVideo 5s 720p 约 119k tokens，具体 profiling 见独立观测）。
- **依赖算子**：blitz_sparse_attention（外部 ops-transformer 仓库编译）。
- **配置**：@2c45117 起在启动 YAML 顶层增加 `sparse:` 段使能（无该段或 `method: no_sparse` 即关闭），`sparse:` 段内联了原独立 [`sparse_config.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/hunyuan-video/hyvideo/sparse/sparse_config.yaml)（@2f82d10 为独立文件形式）的全部字段；`config/single_sparse.yaml` 为单卡 SVG 参考、`config/sp8_sparse.yaml` 为 8 卡 Ulysses + SVG 参考（均 `720*1280*129` 规格）。

模型参数按固定配置文件核对：

- [2c45117 单卡稀疏配置](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/config/single_sparse.yaml)
- [2c45117 八卡稀疏配置](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/config/sp8_sparse.yaml)

`sparse.params.TopK` 与 `sparse.params.SVG` 分开维护各自参数；不复制易发生缩进或同名键覆盖的合并示例。

通过 `python sample_video.py --sparse_method TopK/SVG` 使能。

### 外部依赖与限制

- 依赖外部 blitz_sparse_attention 算子编译：

外部 `ops-transformer` 需使用与固定模型匹配、且已核验的提交及目标 SoC 构建。当前记录未给可复核的外部构建提交时，先停止安装，不能直接拉取滚动分支当作已确认依赖。

- TopK 需要离线 profiling 保存 QK，profile 时长与样本数线性相关
- SVG 仅支持 `sparse_time_step` 内使能，早期 step 变化剧烈不适合稀疏
- 稀疏度设置过高会显著影响画质（ambiguity：源未给出端到端质量指标对比）
- 定量结果统一见[稀疏观测草稿](../../optimizations/benchmark_observations/hunyuan_video_sparse_source_observations.md)，不在启动 Guide 重复维护结果表。
