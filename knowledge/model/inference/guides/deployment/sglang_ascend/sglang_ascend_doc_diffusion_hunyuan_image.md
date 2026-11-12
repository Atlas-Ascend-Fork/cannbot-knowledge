---
type: Guide
title: SGLang Diffusion HunyuanImage3昇腾边界：TP分片与未验证组合
description: 说明四NPU TP4等价启动、encoder/VAE复制及SP/CFG并行未接入，避免容量估算当峰值实测。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/diffusion/Tencent/HunyuanImage3.mdx
  role: primary
created_at: '2026-11-08T12:33:45Z'
updated_at: '2026-11-09T04:30:20Z'
platforms: []
---

# SGLang Diffusion HunyuanImage3昇腾边界：TP分片与未验证组合

## 资源与可达路线

本配方仅针对 HunyuanImage-3.0-Instruct checkpoint，不覆盖另行发布的 distilled 版本。cookbook命令生成器目标为Linux/CUDA；Ascend四可见NPU环境给出等价num-gpus4、TP4、Ulysses1启动。num-gpus统计设备而非固定物理卡，先完成NPU安装，不向该环境安装CUDA extra。精确配方若未显式标记则仍未验证。

此pipeline不实现sequence-parallel attention或CFG并行；TP只分片transformer，vision encoder和VAE仍复制。约160GB BF16 transformer是权重容量估算，不是峰值HBM，需为复制组件、激活与加载buffer留空间。

## 性能与验收

从batch1开始，测试最大参考图数量和输出尺寸的峰值，再调整batching-max-size/delay；prompt/seed不同可合批，不兼容条件或采样不能强合。模型有专用Cache-DiT adapter，复用近似结果需测质量；SP、CFG并行、量化和完整checkpoint CUDA性能并未由此recipe验证，更不能作为NPU支持证据。本次未执行服务或基准，芯片范围未知。

## 配套知识

[MoE归约与多输出](../../integration/sglang_ascend/sglang_ascend_diffusion_hunyuan_image.md)。
