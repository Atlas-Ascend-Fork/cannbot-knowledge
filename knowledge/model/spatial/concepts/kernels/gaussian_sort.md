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
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/gaussian_sort.cpp
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# GaussianSort —— 3DGS tile 内高斯球深度排序算子

Alpha-blending 渲染依赖累乘，必须保证高斯球在每个 tile 内**按深度排序后依次渲染**。`GaussianSort` 负责把每个 tile 命中的高斯球按深度排序，输出排序后的高斯球 ID。host 定义见 [`gaussian_sort.cpp`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/gaussian_sort.cpp)，被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联在精确相交映射之后、渲染之前。

## 算子接口

`GaussianSort`：

- 输入：`lb_sched`（负载均衡调度）、`gaussian_cnt`、`gs_ids`（候选高斯球 ID）、`depths`（深度）、`sorted_offset`（各 tile 排序后偏移）。
- 输出：`sorted_gs_ids`（排序后高斯球 ID）。
- 属性：`max_tile_gauss`(int)。

Python 封装签名见 [`ops/gaussian_sort.py`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/meta_gauss_render/ops/gaussian_sort.py)：`gaussian_sort(lb_sched, gaussian_cnt, depths, gs_ids, sorted_offset, max_tile_gauss)`。

## 在渲染流程中的位置

`rasterizer.py::_ascend_rasterization` 中排序段：

1. `flash_gaussian_build_mask(...)`（[precise-intersection](precise_intersection.md)）输出 `tile_sums / tile_offsets / tile_depths / tile_gauss_ids`。
2. 由 `tile_offsets` 末位（`[:, :, -1]`，shape `[B,C]`）取每个相机 view 的高斯球总数 `sorted_cnts`，flatten 后 `torch.cumsum` 得逐-view 排序偏移 `sorted_offset`。
3. `get_render_schedule(tile_sums_cpu, vector_num)` 给出负载均衡调度 `lb_sched`（贪心策略，详见 [calc-render](calc_render.md) 的负载均衡小节）。
4. `max_tile_gauss = torch.amax(tile_sums)`。
5. `gaussian_sort(lb_sched, tile_sums, tile_depths, tile_gauss_ids, sorted_offset, max_tile_gauss)` → `sorted_gs_ids`。

排序结果按 `sorted_offset` 切片后逐 view 送入 `calc_render`（[calc-render](calc_render.md)）做 alpha-blending。

> 排序键为 tile 内高斯球深度（`depths`/`tile_depths`），保证渲染时由近及远依次混合。该算子未配套独立优化文档，细节以 host/kernel 源码为准（[`op_kernel/gaussian_sort.cpp`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_kernel/gaussian_sort.cpp)）。

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 上游：[precise-intersection](precise_intersection.md)（提供 tile-高斯映射与候选 ID）；下游：[calc-render](calc_render.md)（渲染）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)

<!-- cannbot:related:start -->
## 相关

- [CalcRender —— 3DGS Alpha-blending 渲染融合算子（前向/反向）](calc_render.md)（`related`）：`CalcRender` 是 3DGS 光栅化的核心渲染算子，把空间中已排序的 3D 高斯球颜色 alpha-blending 到各像素上，构成对应视角的渲染图。host 定义为 ［`CalcRenderFwdDoubleClipGsids`］(https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/calc_render_fwd_double_clip_gsids.cpp)（前向）与 ［`CalcRenderBwdVarClipGsids`］(https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/calc_render_bwd_var_clip_gsids.cpp)（反向），由 `rasterizer.py` 中 `calc_render(...)` 调用。被 ［3d-gaussian-splatting］(../algorithms/3d_gaussian_splatting.md) 串联在渲染流程末端。；Alpha-blending 渲染依赖累乘，必须保证高斯球在每个 tile 内**按深度排序后依次渲染**。`GaussianSort` 负责把每个 tile 命中的高斯球按深度排序，输出排序后的高斯球 ID。host 定义见 ［`gaussian_sort.cpp`］(https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/gaussian_sort.cpp)，被 ［3d-gaussian-splatting］(../algorithms/3d_gaussian_splatting.md) 串联在精确相交映射之后、渲染之前。。GaussianSort 产出 tile 内按深度排序的高斯球 ID，CalcRender 以已排序高斯为前提执行顺序敏感的 alpha-blending。
- [Precise Intersection（FlashGaussianBuildMask）—— 3DGS 高斯球-像素块精确相交算子](precise_intersection.md)（`related`）：“`flash_gaussian_build_mask(...)`（［precise-intersection］(precise_intersection.md)）输出 `tile_sums / tile_offsets / tile_depths / tile_gauss_ids`。”；“- 输出：`tile_sum`（每 tile 命中高斯数）、`tile_depths`（排序用深度）、`gauss_index`（命中高斯球 ID）。”。Precise Intersection 生产 GaussianSort 所需的 tile 计数、深度和高斯 ID。
<!-- cannbot:related:end -->
