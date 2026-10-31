---
type: Concept
title: GaussianSort —— 3DGS tile 内高斯球深度排序算子
description: Alpha-blending 渲染依赖累乘，必须保证高斯球在每个 tile 内按深度排序后依次渲染。GaussianSort 负责把每个 tile 命中的高斯球按深度排序，输出排序后的高斯球 ID。host 定义见 gaussian_sort.cpp，被 3d-gaussian-splatting 串联在精确相交映射之后、渲染之前。
tags:
- task.implementation
- topic.rendering
- topic.compilation
- topic.three_dimensional_reconstruction
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/kernels/op_host/gaussian_sort.cpp
  role: supporting
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/algorithms/gaussian_splatting/rasterization/rasterizer.py
  role: implementation
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a2
---

# GaussianSort —— 3DGS tile 内高斯球深度排序算子

Alpha-blending 渲染依赖累乘，必须保证高斯球在每个 tile 内**按深度排序后依次渲染**。`GaussianSort` 负责把每个 tile 命中的高斯球按深度排序，输出排序后的高斯球 ID。host 定义见 [`gaussian_sort.cpp`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/kernels/op_host/gaussian_sort.cpp)，被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联在精确相交映射之后、渲染之前。

## 算子接口

`GaussianSort`：

- 输入：`lb_sched`（负载均衡调度）、`gaussian_cnt`、`gs_ids`（候选高斯球 ID）、`depths`（深度）、`sorted_offset`（各 view 输出段的累计结束偏移，长度 B×C；tile 内偏移由 lb_sched 提供）。
- 输出：`sorted_gs_ids`（排序后高斯球 ID）。
- 属性：`max_tile_gauss`(int)。

Python 封装签名见 [`ops/gaussian_sort.py`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/meta_gauss_render/ops/gaussian_sort.py)：`gaussian_sort(lb_sched, gaussian_cnt, depths, gs_ids, sorted_offset, max_tile_gauss)`。

## 在渲染流程中的位置

`rasterizer.py::_ascend_rasterization` 中排序段：

1. `flash_gaussian_build_mask(...)`（[precise-intersection](precise_intersection.md)）输出 `tile_sums / tile_offsets / tile_depths / tile_gauss_ids`。
2. 由 `tile_offsets` 末位（`[:, :, -1]`，shape `[B,C]`）取每个相机 view 的高斯球总数 `sorted_cnts`，flatten 后 `torch.cumsum` 得逐-view 排序偏移 `sorted_offset`。
3. `get_render_schedule(tile_sums_cpu, vector_num)` 给出负载均衡调度 `lb_sched`（贪心策略，详见 [calc-render](calc_render.md) 的负载均衡小节）。
4. `max_tile_gauss = torch.amax(tile_sums)`。
5. `gaussian_sort(lb_sched, tile_sums, tile_depths, tile_gauss_ids, sorted_offset, max_tile_gauss)` → `sorted_gs_ids`。

排序结果按 `sorted_offset` 切片后逐 view 送入 `calc_render`（[calc-render](calc_render.md)）做 alpha-blending。

> 排序键为 tile 内高斯球深度（`depths`/`tile_depths`），保证渲染时由近及远依次混合。该算子未配套独立优化文档，细节以 host/kernel 源码为准（[`op_kernel/gaussian_sort.cpp`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/kernels/op_kernel/gaussian_sort.cpp)）。

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 上游：[precise-intersection](precise_intersection.md)（提供 tile-高斯映射与候选 ID）；下游：[calc-render](calc_render.md)（渲染）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)
