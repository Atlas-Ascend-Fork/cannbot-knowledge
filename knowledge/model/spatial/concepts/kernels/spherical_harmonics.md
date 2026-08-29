---
type: Concept
title: SphericalHarmonics —— 3DGS 球谐系数→颜色 算子（前向/反向）
description: 球谐（Spherical Harmonics, SH）着色是 3DGS 渲染流程的第一步：由相机到高斯球的视线方向 dirs 与每个高斯球的球谐系数 coeffs 计算出视角相关颜色，再送入投影与渲染。前向 host 定义为 SphericalHarmonicsForward，反向为 SphericalHarmonicsBwd。被 3d-gaussian-splatting 串联在投影之前。
tags:
- task.implementation
- topic.rendering
- topic.compilation
- topic.three_dimensional_reconstruction
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/spherical_harmonics_forward.cpp
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# SphericalHarmonics —— 3DGS 球谐系数→颜色 算子

球谐（Spherical Harmonics, SH）着色是 3DGS 渲染流程的第一步：由相机到高斯球的视线方向 `dirs` 与每个高斯球的球谐系数 `coeffs` 计算出视角相关颜色，再送入投影与渲染。前向 host 定义为 [`SphericalHarmonicsForward`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/spherical_harmonics_forward.cpp)，反向为 [`SphericalHarmonicsBwd`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/spherical_harmonics_bwd.cpp)。被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联在投影之前。

## 算子接口

SH 着色机制：按阶数 `degree` 计算 `(degree+1)^2` 个球谐基函数，与每个高斯球的 SH 系数加权求和，得到**视角相关颜色**（系数数随阶数平方增长）。前/反向 tiling 按阶数 0~4 分配不同 buffer 与每循环任务数（前向 L2/L3/L4 buffer = 6/10/16；反向 D0~D4 bufferLen = 5/5/13/21/27）。

前向 `SphericalHarmonicsForward`：

- 输入：`dirs`（视线方向）、`coeffs`（球谐系数）。
- 输出：`output`（颜色）。
- 属性：`degrees_to_use`(int)。

反向 `SphericalHarmonicsBwd`：

- 输入：`dirs`、`coeffs`、`v_colors`（颜色梯度）。
- 输出：`v_dirs`、`v_coeffs`。
- 属性：`degree`(int, REQUIRED)。

## 阶数约束与渲染流程位置

Python 封装（[`ops/spherical_harmonics.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/meta_gauss_render/ops/spherical_harmonics.py)）限制 SH 阶数 `degrees_to_use` 取值 **0~4**，否则抛 `ValueError`。

在 `rasterizer.py::_ascend_rasterization` 中：先由相机原点与高斯球均值算出归一化视线方向 `rays_d`，取 `k = (sh_degree+1)^2` 个系数，调用 `spherical_harmonics(sh_degree, rays_d.reshape(B,N,3), shs[...].reshape(B,N,k,3))` 得到颜色，再 `+0.5` 并 `clip(min=0)`。`config.py` 默认 `sh_degree=3`，并按 `sh_degree_interval=1000` 在训练中逐步启用更高阶。颜色随后送入 `projection_three_dims_gaussian_fused`（[projection-3dgs](projection_3dgs.md)），其反向 `FullyFusedProjectionBwd` 输出的 `v_colors` 即 SH 反向输入。

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 下游：[projection-3dgs](projection_3dgs.md)（消费 SH 颜色，反向产 `v_colors`）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)

<!-- cannbot:related:start -->
## 相关

- [3D Gaussian Splatting 昇腾 Atlas A2 训推优化实践](../algorithms/3d_gaussian_splatting.md)（`related`）：“球谐（Spherical Harmonics, SH）着色是 3DGS 渲染流程的第一步：由相机到高斯球的视线方向 `dirs` 与每个高斯球的球谐系数 `coeffs` 计算出视角相关颜色，再送入投影与渲染。”与“1. **球谐着色** `spherical_harmonics(sh_degree, rays_d, shs)` —— 由视线方向 + 球谐系数算出每个高斯球颜色。见 ［spherical-harmonics］(../kernels/spherical_harmonics.md)。”提供双方正文证据。算子卡产出视角相关颜色，算法卡把该调用固定为 3DGS 光栅化第一阶段，直接连接单算子合同与整条渲染流水。
<!-- cannbot:related:end -->
