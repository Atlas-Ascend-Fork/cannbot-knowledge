---
type: Runbook
title: 权重加载时全局索引须转本地：分片 vocab embedding 的 padding_idx 本地化 + MTP 权重按 num_hidden_layers 动态剥层
description: 权重加载时全局索引须转本地：分片 vocab embedding 的 padding_idx 本地化 + MTP 权重按 num_hidden_layers 动态剥层。给分片/带 MTP 的模型做权重加载适配时，凡是沿用「全局索引」（padding_idx、层号）的代码，在分片或不同层数的变体上会越界/错位/漏加载。给新变体（不同层数、不同 TP 切分）bringup 时对照。
tags:
- task.debugging
- topic.speculative_decoding
- topic.parallelism
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/377
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/472
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-21T01:48:04Z'
platforms:
- agnostic
---

# 权重加载时全局索引须转本地：分片 vocab embedding 的 padding_idx 本地化 + MTP 权重按 num_hidden_layers 动态剥层

## 适用场景

给分片/带 MTP 的模型做权重加载适配时，凡是**沿用「全局索引」（padding_idx、层号）**的代码，在分片或不同层数的变体上会越界/错位/漏加载。给新变体（不同层数、不同 TP 切分）bringup 时对照。

## 症状 → 根因 → 修法

### A. 分片 vocab embedding 直接透传全局 padding_idx → 越界/掩错

- 场景：把 `nn.Embedding` 按每卡分片词表大小 `input_size_per_partition` 分配（[VocabParallelEmbedding](../../concepts/parallelism/embedding_tp.md)，而非全量 vocab）。
- 根因：传入的 `padding_idx` 是全局下标，直接透传会越界、或在错误分片上掩错本地 token。
- 修法：`padding_idx` 必须**先转成分片本地下标、且只在持有该 token 的分片上生效**（其余分片传 `None`）。

### B. MTP 权重加载硬编码层索引 → 非该层数变体漏剥前缀

- 场景：MTP 权重加载适配器 `adapt_safetensors_field_mtp` 原先硬编码 MTP 层索引 `layers.43.`。
- 根因：对 `num_hidden_layers != 43` 的变体（如 dsv4 pro）会漏剥 MTP 层前缀、致 MTP 权重名不匹配、加载失败。
- 修法：MTP 块位于主干层之后、索引 = `config.num_hidden_layers`，须**按此动态剥层**，不写死 43。

## 通用先验

- 权重加载里凡出现「全局 padding_idx / 硬编码层号 / 全量 vocab 假设」，在分片或变体层数下都要**换成分片本地 / config 推导的动态值**。
- 症状「某权重漏加载 / embedding 掩错 / MTP 名不匹配」优先查是否用了未本地化的全局索引。

## 风险 / 边界

- padding_idx 本地化要正确判「哪个分片持有该 token」；MTP 层号 = num_hidden_layers 是该模型族的结构约定，迁移前确认 MTP 块位置。

## 相关经验

- 给新模型接入 MTP 推测解码的完整流程见 [mtp-speculative-decode-model-onboarding](../../guides/integration/mtp_speculative_decode_model_onboarding.md)。
- 量化权重加载布局/命名门控见 [quant-weight-load-layout-and-naming](../../optimizations/rules/quant_weight_load_layout_and_naming.md)。

## Evidence

- `diff 事实`（@6cb4995）：分片 VocabParallelEmbedding 的 padding_idx 转本地下标、非持有分片传 None。
- `diff 事实`（@c0be938）：MTP 层索引 = `config.num_hidden_layers` 动态剥层，非硬编码 43。
- 溯源下探：[cann-recipes-infer-pr-472-fix-shard-vocabparallelembedding-weight-at-init](https://gitcode.com/cann/cann-recipes-infer/merge_requests/472)、[cann-recipes-infer-pr-377-fix-fix-mtp-weight-load](https://gitcode.com/cann/cann-recipes-infer/merge_requests/377)