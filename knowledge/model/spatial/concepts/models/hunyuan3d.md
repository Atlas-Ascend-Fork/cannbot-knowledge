---
type: Concept
title: Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）
description: Hunyuan3D 2.0 通过 DiT 与 VAE 从图像生成形状，再由 Paint 为 mesh 生成纹理；本页说明两阶段输入输出和固定 Atlas A2 适配边界。
tags:
- task.design
- topic.three_dimensional_reconstruction
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/models/Hunyuan3D/Hunyuan3D_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/models/Hunyuan3D/minimal_demo_npu.py
  role: implementation
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a2
---

# Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）

Hunyuan3D 的流水线分为形状生成和纹理生成两阶段，产出带纹理贴图的三维 mesh。

- **shapegen（Hunyuan3D-DiT，1.1B）**：图像输入经 DiT 扩散采样、VAE 几何解码生成 mesh，支持单视角与 Hunyuan3D-2mv 多视角输入。
- **texgen（Hunyuan3D-Paint，1.3B）**：消费 mesh 与图像，经多视角光栅化、delight 和 bake 生成纹理贴图。

## 适配边界

Recipes 在上游网络代码之上提供 Atlas A2 单机单卡 NPU 适配，证据不覆盖上游全部实现。具体算子替换、编译和缓存能力绑定固定适配版本；该入口在启用非 NoCache 方法时自动关闭 full_graph，不能将图模式与缓存收益叠加。

## 实践入口

- [推理优化与来源观测](../../optimizations/hunyuan3d_a2_inference.md)
- [部署与验收](../../guides/deployment/hunyuan3d_a2_deployment.md)

## Links

Hunyuan3D 的计算模块与优化机制：
- [dit](../../../inference/concepts/modules/dit.md) — DiT 是 shapegen 形状生成主干；Hunyuan3D 是其 3D 图生场景部署。
- [dit-cache](../../../inference/concepts/techniques/dit_cache.md) — Hunyuan3D 在非 CFG 串行场景中使用 FBCache、TeaCache 与 TaylorSeer，缓存阈值和跳过间隔影响生成精度与加速比。
- [vae](../../../inference/concepts/modules/vae.md) — VAE geo_decoder 负责几何解码，与 DiT 一同入图编译。
- [torchair](../../../inference/concepts/frameworks/torchair.md) — `--full_graph` 经 torchair 后端 `torch.compile` 入图。
- [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md) — 图模式优化（计算图优化/多流/内存复用/模型下沉/tiling 下沉）。
- [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md) — FIA 替换 `npu_fusion_attention`，是 DiT/VAE 整图编译的前置条件。
- [multi-stream](../../../inference/concepts/techniques/multi_stream.md) — TaylorSeer offload 用 copy/cal 双流 + event 重叠搬运与计算。
- [ascendc](../../../inference/concepts/frameworks/ascendc.md) — render_npu / 自研光栅化小算子的实现底座。
- [atlas-a2](../platforms/atlas_a2.md) — 目标平台。

源：[cann-recipes-spatial-intelligence](https://gitcode.com/cann/cann-recipes-spatial-intelligence/tree/0d955a020eed3ac1f274e5ab26f792b02b011728)
