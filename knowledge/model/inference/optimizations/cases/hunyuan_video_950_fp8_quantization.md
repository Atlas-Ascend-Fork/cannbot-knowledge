---
type: Optimization
title: HunyuanVideo 950 FP8 量化接入与验证案例
description: 保留单卡/Ulysses8的量化接入与质量边界，完整性能数字统一引用平台观测。
tags:
- task.optimization
- topic.diffusion
- topic.precision
status: stable
platforms:
- '950'
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/dfa1a889e6787d03c7c535e968c694a59114182f/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
      quantization:
      - fp8
created_at: '2026-10-21T01:48:04Z'
updated_at: '2026-10-21T09:56:26Z'
---


# HunyuanVideo 950 FP8 量化接入与验证案例

## 条件与实现

来源为 PR325 固定提交，平台 950PR、HunyuanVideo 720p 129 帧，比较单卡及 Ulysses8。实现与适用性统一见 [FP8 量化规则](../rules/video_dit_fp8_mxfp8_quantization.md)。

## 优先级 · 收益分解（950PR / HunyuanVideo 720p 129 帧，仓自报无独立复测）

完整单卡/Ulysses8对照数字由[950PR来源性能观测](../benchmark_observations/hunyuan_video_950_source_benchmark.md)维护；本卡只保留接入差异，不另维护第二份收益排序。

FP8 Attention与MXFP8 Matmul是可分别对照的两类替换，VAE不在这一组量化对象内。单卡与Ulysses8分别验收，量化FA的Ring限制不能由其他稀疏Ring能力推导解除。

## 验证边界

来源缺量化后质量/视频相似度指标。实际采用前保持权重、prompt、seed、采样步和并行配置一致，分别验收质量、端到端、峰值内存和量化分支；不能从整网速度把任何算子描述成跨模型必选项。本次未执行硬件、精度或回退实验。
