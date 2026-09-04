---
type: Concept
title: 3D Gaussian Splatting 昇腾 Atlas A2 训推优化实践
description: 3D Gaussian Splatting（3DGS）是 2023 年由 Kerbl 等人提出的可微渲染算法，以 3D 高斯椭球为核心图元，通过可微光栅化完成三维场景的重建与渲染（Kerbl et al., ACM TOG 2023）。cann-recipes-spatial-intelligence 提供了基于 gsplat 框架的昇腾适配版本，在 Atlas A2 上支持单卡训练与推理，并通过一组 AscendC 自研融合算子重写了 GPU 实现中的关键流程；实现与测量证据限于该昇腾适配版本，不覆盖 gsplat 完整实现。
tags:
- task.design
- topic.three_dimensional_reconstruction
- topic.rendering
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_precise_intersection_optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a2
---

# 3D Gaussian Splatting 昇腾 Atlas A2 训推优化实践

3D Gaussian Splatting（3DGS）是 2023 年由 Kerbl 等人提出的可微渲染算法，以 **3D 高斯椭球**为核心图元，通过可微光栅化完成三维场景的重建与渲染（Kerbl et al., *ACM TOG* 2023）。`cann-recipes-spatial-intelligence` 提供了 3DGS 的昇腾适配版本，基于 [gsplat](https://github.com/nerfstudio-project/gsplat) 框架，在 **Atlas A2** 上支持单卡训练与推理，并通过一组 AscendC 自研融合算子重写了 GPU 实现中的关键流程。各算子的实现细节见下方链接的 kernel 页。

## 高斯球表示与渲染流程

3DGS 用一组 3D 高斯椭球表示场景，每个高斯球带均值 `means`、四元数 `quats`、缩放 `scales`、不透明度 `opacities`、球谐系数（`sh0`/`shN`）。渲染（光栅化）流程在 [`rasterization/rasterizer.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/algorithms/gaussian_splatting/rasterization/rasterizer.py) 的 `_ascend_rasterization` 中实现，内部按顺序调用并串联各自研算子（导入自 [`meta_gauss_render`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/meta_gauss_render/__init__.py)）：

1. **球谐着色** `spherical_harmonics(sh_degree, rays_d, shs)` —— 由视线方向 + 球谐系数算出每个高斯球颜色。见 [spherical-harmonics](../kernels/spherical_harmonics.md)。
2. **投影 + 视锥剔除** `projection_three_dims_gaussian_fused(...)` —— 把 3D 高斯球的均值/协方差投影到 2D 平面（`means2d`/`conics`/`radius`/`covars2d`），并融合视锥剔除。投影见 [projection-3dgs](../kernels/projection_3dgs.md)，剔除（`GaussianFilter`）见 [gaussian-filter](../kernels/gaussian_filter.md)。
3. **高斯球-像素块映射 + 排序** `flash_gaussian_build_mask(...)` 计算高斯球与 tile 的精确相交关系（Precise Intersection，见 [precise-intersection](../kernels/precise_intersection.md)），`get_render_schedule(...)` 给出负载均衡调度，`gaussian_sort(...)` 按 tile 排序高斯球。排序见 [gaussian-sort](../kernels/gaussian_sort.md)。
4. **Alpha-blending 渲染** `calc_render(...)` —— 按 tile 累积颜色与深度，输出渲染图。见 [calc-render](../kernels/calc_render.md)。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/gs_algorithm.png" width="55%">

<sub>传统 GS 高斯球-像素块映射原理（正切边界框）。来源：[precise_intersection 优化文档](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_precise_intersection_optimization.md)。</sub>

## SIMD 架构适配总览

对比 GPU 的 Warp 级调度，昇腾 Atlas A2 为 SIMD（Vector）架构，3DGS 需要专门改写。`cann-recipes-spatial-intelligence` README 列出四类核心优化（详见各 kernel 页）：

| 优化点 | 落地算子/页面 | 一句话 |
| --- | --- | --- |
| Alpha-blending 融合算子 + 流水/剪枝 | [calc-render](../kernels/calc_render.md) | 指令流水并行、Double Buffer、两级高斯球剪枝 |
| 视锥剔除融合算子 | [gaussian-filter](../kernels/gaussian_filter.md) | `GaussianFilter` 融合剔除 + 反向 Scatter 还原 |
| 高斯负载均衡 | [calc-render](../kernels/calc_render.md) | 贪心「先重后轻、分给最轻」分配 tile 到 Vector 核 |
| Precise Intersection 融合算子 | [precise-intersection](../kernels/precise_intersection.md) | 基于 FlashGS 的精确相交判断 + Vector-MTE 流水并行 |

这些算子全部以 **AscendC** 自研实现（详见 [ascendc](../../../inference/concepts/frameworks/ascendc.md)，本项目用其实现 SIMD 架构下的可微渲染算子）。

## 算子清单（host 定义）

[`ops/ascendc/kernels/op_host/`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/) 下定义的自研算子：`SphericalHarmonicsForward`/`SphericalHarmonicsBwd`、`ProjectionThreeDimsGaussianForward`/`FullyFusedProjectionBwd`、`QuatScalesToCovars`、`GaussianFilter`、`FlashGaussianBuildMask`、`GaussianSort`、`CalcRenderFwdDoubleClipGsids`/`CalcRenderBwdVarClipGsids`。算子接口测试见 [`ops/ascendc/tests/`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/tests/)。

## 训推配置与启动

- 环境：CANN 8.2.RC1、`torch` 2.1.0 + `torch_npu` 2.1.0.post12、Python 3.8、单卡 Atlas A2。
- 自研算子需先编译安装：`cd ops/ascendc && bash build.sh --python=3.8`，再 `pip install dist/*.whl`（[build.sh](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/build.sh)）。
- 数据集：在 `algorithms/gaussian_splatting/` 下运行 [`datasets/download_dataset.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/algorithms/gaussian_splatting/datasets/download_dataset.py) 下载 mipnerf360 (`360_v2`) 到 `data/360_v2/`。
- 训练：`ASCEND_RT_VISIBLE_DEVICES=1 python train.py`；推理：`python train.py --ckpt path_to_ckpt.pt`；全场景：`bash train_all.sh`。

关键配置（[`rasterization/config.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/algorithms/gaussian_splatting/rasterization/config.py)）：`tile_size=32`、`sh_degree=3`、`max_steps=30000`、`camera_model="pinhole"`、`near_plane=0.01`、`far_plane=1e10`、`batch_size=1`。

## Benchmark（汇总，详见各 kernel 页）

均在含 13 万高斯球（过滤后约 6.8 万渲染高斯球）场景、训练 30000 iters 下测得（mipnerf360_v2，部分按 garden 场景）：

- Alpha-blending 流水 + 剪枝：前向约 10%、反向约 30% 收益（`alpha` 阈值 0.004 时反向 18.71→13.11 ms）。
- 负载均衡：前向、反向均约 23% 收益。
- Precise Intersection 流水并行 15.2% + 计算优化 26.7% + 过滤优化 18.8%；相比传统 GS 算法渲染前向显著降低（如 100w 高斯/425 块：35.957→22.880 ms）。

> 上游开源本体 3DGS（INRIA repo-sam）与 gsplat、FlashGS 算法见 [arXiv:2408.07967](https://arxiv.org/abs/2408.07967)；以上数据均来自 `cann-recipes-spatial-intelligence` 的昇腾实现。

## 相关页面

- 算子页：[calc-render](../kernels/calc_render.md)、[projection-3dgs](../kernels/projection_3dgs.md)、[spherical-harmonics](../kernels/spherical_harmonics.md)、[gaussian-sort](../kernels/gaussian_sort.md)、[precise-intersection](../kernels/precise_intersection.md)、[gaussian-filter](../kernels/gaussian_filter.md)
- 平台：[atlas-a2](../platforms/atlas_a2.md)（单卡 Atlas A2 训推）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)

<!-- cannbot:related:start -->
## 相关

- [CalcRender —— 3DGS Alpha-blending 渲染融合算子（前向/反向）](../kernels/calc_render.md)（`related`）：CalcRender 在 3DGS 光栅化末端对按深度排序的高斯球执行 alpha-blending，输出渲染颜色和深度。
- [GaussianFilter —— 3DGS 视锥剔除融合算子（前向/反向 Scatter）](../kernels/gaussian_filter.md)（`related`）：GaussianFilter 与 3DGS 投影一同执行视锥剔除，减少后续排序和渲染的高斯球数量，并在反向通过 Scatter 还原梯度。
- [Precise Intersection（FlashGaussianBuildMask）—— 3DGS 高斯球-像素块精确相交算子](../kernels/precise_intersection.md)（`related`）：Precise Intersection 在 3DGS 投影之后计算高斯球到 tile 的精确命中映射，供后续排序和渲染使用。
- [Projection-3DGS —— 3D→2D 高斯球投影融合算子（前向/反向）](../kernels/projection_3dgs.md)（`related`）：Projection-3DGS 将场景高斯球转换为 `means2d`、`conics`、`covars2d` 等 2D 投影属性，供精确相交与排序使用。
- [SphericalHarmonics —— 3DGS 球谐系数→颜色 算子（前向/反向）](../kernels/spherical_harmonics.md)（`related`）：SphericalHarmonics 在 3DGS 光栅化第一阶段根据视线方向和球谐系数生成视角相关颜色，供后续投影与渲染使用。
<!-- cannbot:related:end -->
