---
type: Concept
title: Projection-3DGS —— 3D→2D 高斯球投影融合算子（前向/反向）
description: 投影预处理把 3D 高斯球的均值与协方差由 3D 球面投影到 2D 平面，得到光栅化所需的 2D 均值 means2d、协方差/锥参 conics/covars2d、深度 depths、半径 radius 等属性。前向 host 定义为 ProjectionThreeDimsGaussianForward，反向为 FullyFusedProjectionBwd；Python 侧 projection_three_dims_gaussian_fused(...) 在融合投影的同时执行视锥剔除（见 gaussian-filter）。被 3d-gaussian-splatting 串联在球谐着色之后、排序之前。
tags:
- task.implementation
- topic.rendering
- topic.compilation
- topic.three_dimensional_reconstruction
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/projection_three_dims_gaussian_forward.cpp
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-13T00:00:00Z'
platforms:
- a2
---

# Projection-3DGS —— 3D→2D 高斯球投影融合算子

投影预处理把 3D 高斯球的均值与协方差由 3D 球面投影到 2D 平面，得到光栅化所需的 2D 均值 `means2d`、协方差/锥参 `conics`/`covars2d`、深度 `depths`、半径 `radius` 等属性。前向 host 定义为 [`ProjectionThreeDimsGaussianForward`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/projection_three_dims_gaussian_forward.cpp)，反向为 [`FullyFusedProjectionBwd`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/fully_fused_projection_bwd.cpp)；Python 侧 `projection_three_dims_gaussian_fused(...)` 在融合投影的同时执行视锥剔除（见 [gaussian-filter](gaussian_filter.md)）。被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联在球谐着色之后、排序之前。

## 前向算子接口

`ProjectionThreeDimsGaussianForward`：

- 输入：`means`（3D 均值）、`covars`（3D 协方差）、`viewmats`（视图矩阵）、`ks`（相机内参）。
- 输出：`means2d`、`depths`、`conics`、`compensations`、`det`、`radius`、`covars2d`。
- 属性：`image_width`、`image_height`、`eps2d`、`calc_compensations`(bool)、`camera_model`(int)。

`camera_model` 与 `config.py` 的 `camera_model: "pinhole" | "ortho" | "fisheye"`（默认 `pinhole`）对应；`eps2d` 是 2D 协方差膨胀项。3D 协方差由 `QuatScalesToCovars`（[`quat_scales_to_covars.cpp`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/quat_scales_to_covars.cpp)，输入 `quat`/`scales`，输出 `covars`）由四元数与缩放生成。

## 反向算子接口

`FullyFusedProjectionBwd`：

- 输入：`means / quats / scales / conics / viewmats / Ks / v_means2d / v_depths / v_conics / v_colors_culling / v_opacities_culling / filter / compesations`；属性 `width / height`（REQUIRED）。
- 输出：`v_pW / v_quats / v_scales / v_R / v_colors / v_opacities`。

反向把投影、球谐颜色与不透明度梯度融合（`fully_fused`），且接收前向产生的 `filter`：**计算前先做反视锥剔除还原原始 Tensor**，无效高斯的梯度自然置 0（与 [gaussian-filter](gaussian_filter.md) 的 Scatter 还原配套）。`v_colors_culling`/`v_opacities_culling` 即来自渲染/球谐反向、按 culling 后紧凑布局的梯度。

## 视锥剔除（融合点）

视锥剔除融合进投影预处理：前向输出 `radius`/`covars2d`/`conics` 后，`GaussianFilter` 据此剔除深度越界、2D 椭圆退化、屏幕外的高斯，返回比特掩码 `filter` 与有效计数 `cnt`，供后续排序/渲染只处理有效高斯。详见 [gaussian-filter](gaussian_filter.md)。

## 在渲染流程中的位置

`rasterizer.py::_ascend_rasterization` 中：球谐着色 → `projection_three_dims_gaussian_fused(...)`（投影 + 剔除，得 `means2d/depths/conics/opacities/radius/covars2d/colors/cnt`）→ `flash_gaussian_build_mask` 算精确相交 → `gaussian_sort` 排序 → `calc_render` 渲染。

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 配套：[gaussian-filter](gaussian_filter.md)（视锥剔除 + 反向 Scatter 还原）、[spherical-harmonics](spherical_harmonics.md)（颜色来源）
- 下游：[precise-intersection](precise_intersection.md)（消费本算子产出的 2D 投影属性 means2d/conics/covars2d 算高斯-tile 精确相交）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)
