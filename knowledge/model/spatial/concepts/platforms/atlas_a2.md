---
type: Concept
title: Atlas A2（空间智能样例目标平台）
description: 华为昇腾 Atlas A2 系列训练/推理服务器，是 cann-recipes-spatial-intelligence 仓所有样例（VGGT、Hunyuan3D、3D Gaussian Splatting）的目标部署平台。各样例 README 明确以 Atlas A2 为运行环境（3DGS 为单卡 Atlas A2 训推）。
tags:
- task.lookup
- topic.architecture
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/models/vggt/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/models/Hunyuan3D/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/algorithms/gaussian_splatting/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a2
---

# Atlas A2（空间智能样例目标平台）

华为昇腾 **Atlas A2** 系列训练/推理服务器，是 `cann-recipes-spatial-intelligence` 仓所有样例（[VGGT](../models/vggt.md)、[Hunyuan3D](../models/hunyuan3d.md)、[3D Gaussian Splatting](../algorithms/3d_gaussian_splatting.md)）的目标部署平台。各样例 README 明确以 Atlas A2 为运行环境（3DGS 为**单卡 Atlas A2** 训推）。

> `cann-recipes-spatial-intelligence` 样例声明目标平台为「Atlas A2」，未提供其算力、die、HBM 等硬件规格；硬件细节以昇腾官方资料为准。

## 各样例的 CANN / 框架版本

| 样例 | CANN | torch / torch_npu | Python |
|---|---|---|---|
| VGGT | 8.5.0 | 2.7.1 / 2.7.1.post2 | 3.11 |
| 3D Gaussian Splatting | 8.2.RC1 | 2.1.0 / 2.1.0.post12 | 3.8 |
| Hunyuan3D | 8.2.RC1 | 2.6.0 / 2.6.0.post3 | 3.10 |

版本差异源于各样例独立适配；各版本组合的适用范围限于对应样例 README。

## Links

- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：推理域目标平台 Atlas A3，与 A2 同属昇腾 Atlas 系列；A3 页含代际/规格对照）
- [vggt](../models/vggt.md)（在本平台推理）
- [hunyuan3d](../models/hunyuan3d.md)（在本平台推理）
- [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)（单卡 Atlas A2 训推）
- [cann-recipes-spatial-intelligence](https://gitcode.com/cann/cann-recipes-spatial-intelligence/tree/0d955a020eed3ac1f274e5ab26f792b02b011728)
- 跨域·具身：[agibot-arm-world-model](../../../embodied/concepts/world_models/agibot_arm_world_model.md)、[ascend-310p](../../../embodied/concepts/platforms/ascend_310p.md)、[ddp-static-graph](../../../embodied/concepts/techniques/ddp_static_graph.md)、[gradient-checkpoint-refine](../../../embodied/concepts/techniques/gradient_checkpoint_refine.md)（具身样例在 Atlas A2 的训练 / 推理（平台 family））
