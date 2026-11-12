---
type: Guide
title: SGLang Diffusion MiniMax-H3昇腾配方：驻留、TP/SP与有损缓存
description: 保留4/8 NPU LASER配方和单次历史延迟，说明请求quality覆盖及无缓存基线。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/MiniMax/MiniMax-H3.mdx
  role: primary
created_at: '2026-11-08T12:33:45Z'
updated_at: '2026-11-09T04:31:21Z'
platforms: []
---

# SGLang Diffusion MiniMax-H3昇腾配方：驻留、TP/SP与有损缓存

## 来源配方

来源Ascend示例使用MiniMax-H3的fl2va变体：8 NPU为TP2/SP4，4 NPU为TP2/SP2，LASER attention；可将后端换FA但需重新验收。DiT显式dit-cpu-offload=false留在NPU，text_encoder使用layerwise-offload，HCCL_BUFFSIZE256。驻留选择降低反复传权重成本，同时提高HBM需求，不能仅按transformer shard估计峰值。

测量命令启用Cache-DiT：FN2/BN1/warmup4/RDT0.4/MC4/TaylorSeer order2。这类 Ascend 手工缓存配方须省略请求 `quality` 字段：任何显式 quality（包括 exact/lossless）都会退出通用 Cache-DiT 路径；high 仅覆盖来源已审计的4×H200场景，不能用于此NPU配方。建立无缓存基线时可清除缓存开关/环境变量，或按请求级 exact/lossless 关闭通用缓存，仍须核对采样设置；缓存不是数值无损。来源5秒T2VA、1344×768、124帧、24fps、50步，8/4 NPU分别55.07/103.57秒，均是单次E2E，不是平均或本次实测；来源未为此节逐一标产品型号，平台保持未知。

## 验收

先确认变体、音视频条件和采样协议；num_inference_steps=N执行N次更新并使用N+1个sigma点，参考实现若按sigma数计步应对齐。先无缓存做质量基线，再对比缓存、attention、并行与offload，分别记录首次加载/编译、warmup和稳态。失败逐项回退，不能用GPU近似attention或量化表证明NPU支持。本次未运行上游模型。

## 配套知识

[H3循环与VAE实现](../../integration/sglang_ascend/sglang_ascend_diffusion_minimax_h3.md)；[LASER精度与padding](../../integration/sglang_ascend/sglang_ascend_diffusion_laser.md)。
