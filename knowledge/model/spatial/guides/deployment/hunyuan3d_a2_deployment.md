---
type: Guide
title: Hunyuan3D A2 部署与验收
description: 固定 Atlas A2 单卡 Hunyuan3D 适配的环境、权重、启动开关、图模式与缓存互斥及验收回退步骤。
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
created_at: '2026-10-29T09:38:05Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- a2
---

# Hunyuan3D A2 部署与验收

前置环境为固定来源的 CANN 8.2.RC1、torch/torch_npu 2.6、Atlas A2 单卡，准备对应上游代码和权重后，在 Recipes 的 models/Hunyuan3D 工作目录启动。

```bash
source set_env.sh   # 把 module 优化模块（含 dit_cache）加入环境变量
python minimal_demo_npu.py --model_path tencent/Hunyuan3D-2 \
  --multiview --face_reduce --full_graph --multi_thread --save_render
```
`--full_graph` 仅在 `cache_name == "NoCache"` 生效；配置 FBCache、TeaCache 或 TaylorSeer 会自动关闭图模式，单视角/多视角均如此。先按 NoCache 建立质量与计时基线，再单独验收图模式或缓存，不能累加两组来源收益。

开关：`--multiview` 多视角；`--face_reduce` 减面；`--full_graph` 图模式；`--multi_thread` 多线程并行光栅化；`--use_render_npu` NPU 光栅化（与 `--multi_thread` 互斥）；`--save_render` 复用光栅化结果。

权重支持 Hunyuan3D-DiT-v2-0（单视角）、Hunyuan3D-DiT-v2-mv（多视角）、Hunyuan3D-Paint-v2-0（纹理）、Hunyuan3D-Delight-v2-0（去高光），默认 `base_dir=~/.cache/hy3dgen/`。


## 验证与停止条件

保存镜像、依赖、权重、输入图、随机种子和实际生效开关；核对 mesh 与纹理是否完整，分别记录 shapegen/texgen 时延与质量。编译失败、模型输出异常或质量下降时恢复 NoCache 与非图基线，关闭相应优化后重新检查。来源 benchmark 见[优化与观测](../../optimizations/hunyuan3d_a2_inference.md)，模型阶段关系见[模型概念](../../concepts/models/hunyuan3d.md)。
