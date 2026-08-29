---
type: Concept
title: Precise Intersection（FlashGaussianBuildMask）—— 3DGS 高斯球-像素块精确相交算子
description: Precise Intersection 算子用于计算高斯球-像素块（tile）映射关系，基于 FlashGS 算法（外部论文，未克隆未核验）实现。host 定义为 FlashGaussianBuildMask，Python 侧为 flash_gaussian_build_mask(...)。被 3d-gaussian-splatting 串联在投影之后、排序之前，输出供 gaussian-sort 排序、calc-render 渲染。
tags:
- task.implementation
- topic.rendering
- topic.compilation
- topic.three_dimensional_reconstruction
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_precise_intersection_optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a2
---

# Precise Intersection —— 3DGS 高斯球-像素块精确相交算子

Precise Intersection 算子用于计算高斯球-像素块（tile）映射关系，基于 [FlashGS 算法](https://arxiv.org/abs/2408.07967)实现。host 定义为 [`FlashGaussianBuildMask`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/flash_gaussian_build_mask.cpp)，Python 侧为 `flash_gaussian_build_mask(...)`。被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联在投影之后、排序之前，输出供 [gaussian-sort](gaussian_sort.md) 排序、[calc-render](calc_render.md) 渲染。

## 算子接口

`FlashGaussianBuildMask`：

- 输入：`means2d / opacity / conics / covars2d / depths / cnt / tile_grid / gather_mask`。
- 输出：`tile_sum`（每 tile 命中高斯数）、`tile_depths`（排序用深度）、`gauss_index`（命中高斯球 ID）。
- 属性：`image_width`(float)、`image_height`(float)、`tile_size`(int)。

## GS 算法 vs Precise Intersection

预处理后高斯球已由 3D 投影到 2D 平面。传统 GS 算法以投影中心为圆心、长半径 `Radii` 为半径作圆的正切**正方形**边界框，与 tile 有相交面积即认为相交并加入排序/渲染。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/gs_algorithm.png" width="50%">

<sub>传统 GS 正切边界框原理。来源：[precise_intersection 优化文档](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_precise_intersection_optimization.md)。</sub>

由于 2D 投影为椭圆，正方形框会把未真正重叠的高斯球纳入排序/渲染，增大计算量。Precise Intersection 的优化：① 用与椭圆相切的**矩形**边界框（比正方形更精准）；② 对与边界框重合的 tile，进一步判断是否与椭圆相交——为降低二次方程求解成本，转化为「判断椭圆在边界框上的投影是否与边界框重叠」。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/flashgs_algorithm.png" width="65%">

<sub>Precise Intersection 原理（矩形框 + 椭圆投影相交判断）。来源同上 precise_intersection 文档。</sub>

计算流程（每个 tile 对全部高斯）：① 算相切矩形顶点坐标；② 判断边界框是否与 tile 相交得掩码 `mask`；③ 判断高斯球中心是否在 tile 范围内得 `centerFlag`；④ 判断 tile 边界是否与高斯投影相交得 `intersectFlag`；⑤ 三掩码与或得最终映射掩码。

## Tiling 设计

仅用 Vector 核。以**像素块数 `M`** 作为总任务分核：每核约 `M/blockDim` 个 tile；因 `M` 与 `blockDim` 非倍数，用大小核策略——前 `n` 核算 `K` 个、后 `blockDim-n` 核算 `K-1` 个。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/flashgs_tiling_1.png" width="60%">

<sub>大小核分核。来源同上 precise_intersection 文档。</sub>

切块：对高斯球分块搬入 UB 与各核 tile 计算。UB 的 **85%** 用于高斯球搬入/搬出/分块计算，**15%** 留给计算 API 临时结果；一次切块算约 **2.62K** 高斯球。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/flashgs_block.png" width="60%">

<sub>UB 切块（85% + 15%）。来源同上 precise_intersection 文档。</sub>

## Vector-MTE 流水并行优化

原始线性流水中 MTE2→Vector→MTE3 串行（每步插同步），高斯球 10w~100w 时浪费大。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/flashgs_timeline_1.png" width="60%">

<sub>原始线性流水。来源同上 precise_intersection 文档。</sub>

优化点：① 当前分块算完，**MTE3 搬出与下一分块计算并行**（搬出数据与下一块独立），省一次同步；② 若当前块是 Vector 核最后一个 tile 的计算，**计算中同步搬入下次分块所需高斯数据**，使下次计算不必等 MTE2，再省一次同步。garden 场景：搬出并行 4.550→4.216（7.9%），再加搬入并行→3.948（6.8%），总收益 15.2%。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/flashgs_timeline_2.png" width="60%">

<sub>流水并行。来源同上 precise_intersection 文档。</sub>

## 计算优化

高斯球本身属性（2D 投影坐标、协方差逆、不透明度）不随 tile 变化，故把计算拆解为**高斯球相关特征计算**（边界框、不透明度对数等）+ **高斯球-tile 映射计算**，分块时先算前者再逐 tile 算后者，减少重复搬入。此外减少上下文依赖以减少 AscendC 编译器自动插入的 Vector 同步——如边界框 $w=\lfloor\sqrt{2 cov_{00} power}+1\rfloor$、$h=\lfloor\sqrt{2 cov_{11} power}+1\rfloor$ 分三步同步算相同/相近部分（$w_0,h_0$ → $w_1,h_1$ → $w,h$）。garden：流水并行 3.948 → +计算拆解 3.260（21.1%）→ +计算过程调整 3.116（4.6%），总收益 26.7%。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/flashgs_timeline_3.png" width="60%">

<sub>计算拆解后流水。来源同上 precise_intersection 文档。</sub>

## 高斯球坐标初筛 + 掩码过滤

因按 `M` 分核，各核 tile 的纵坐标范围不完全重叠（如图像 144×1440、tile 32×32 共 160 块，第 1 核 4 块 Y 范围 [0,36]…）。故相交计算前对高斯球**纵坐标初筛**，过滤 Y 不在本核范围的高斯，约可滤掉 **90%**，后续只需循环 2-3 次。掩码过滤：把初筛/`mask` 后的有效高斯属性与索引保存，`centerFlag`/`intersectFlag` 仅对前一轮有效高斯计算，避免冗余。采样测试该两项总收益 18.8%（如 140w 高斯/425 块 2.986→2.313, 29.1%）。

「基线方法」指已应用流水并行 + 计算优化的 Precise Intersection；「过滤优化」指在基线上再叠加高斯球坐标初筛 + 掩码过滤（mipnerf360_v2 采样、前向 device 耗时 ms）：

| 高斯球数量 | 像素块数量 | 优化方法 | 前向device耗时(ms) | 收益比例 |
| :--------: | :--------: | :--------: | :--------: | :--------: |
| 20w | 425 | 基线方法 / **过滤优化** | 0.656 / **0.593** | 10.7% |
| 40w | 425 | 基线方法 / **过滤优化** | 1.039 / **0.911** | 14.0% |
| 60w | 425 | 基线方法 / **过滤优化** | 1.270 / **1.213** | 4.7% |
| 80w | 425 | 基线方法 / **过滤优化** | 1.610 / **1.414** | 13.9% |
| 100w | 425 | 基线方法 / **过滤优化** | 1.992 / **1.663** | 19.8% |
| 140w | 425 | 基线方法 / **过滤优化** | 2.986 / **2.313** | 29.1% |
| 170w | 425 | 基线方法 / **过滤优化** | 3.218 / **2.534** | 27.0% |
| 200w | 425 | 基线方法 / **过滤优化** | 3.915 / **3.995** | 30.3% |
| 300w | 425 | 基线方法 / **过滤优化** | 5.462 / **4.558** | 19.8% |

<sub>高斯球坐标初筛 + 掩码过滤收益（总体 18.8%）。来源：[precise_intersection 优化文档 §高斯球坐标初筛优化/掩码过滤优化](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_precise_intersection_optimization.md#掩码过滤优化)。</sub>

## 性能（vs 传统 GS，渲染前向 device 耗时 ms）

| 高斯数 | 像素块 | GS | Precise Intersection |
| --- | --- | --- | --- |
| 20w | 425 | 8.955 | 6.671 |
| 40w | 425 | 17.499 | 13.017 |
| 100w | 425 | 35.957 | 22.880 |
| 7w | 1107 | 7.783 | 4.863 |
| 14w | 1107 | 15.384 | 9.489 |
| 28w | 1107 | 25.311 | 15.493 |

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 上游：[projection-3dgs](projection_3dgs.md)（提供 2D 投影属性）；下游：[gaussian-sort](gaussian_sort.md)、[calc-render](calc_render.md)
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)

<!-- cannbot:related:start -->
## 相关

- [3D Gaussian Splatting 昇腾 Atlas A2 训推优化实践](../algorithms/3d_gaussian_splatting.md)（`related`）：“3DGS 用一组 3D 高斯椭球表示场景，每个高斯球带均值 `means`、四元数 `quats`、缩放 `scales`、不透明度 `opacities`、球谐系数（`sh0`/`shN`）。渲染（光栅化）流程在 ［`rasterization/rasterizer.py`］(https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/algorithms/gaussian_splatting/rasterization/rasterizer.py) 的 `_ascend_rasterization` 中实现，内部按顺序调用并串联各自研算子（导入自 ［`meta_gauss_render`］(https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/meta_gauss_render/__init__.py)）：”与“Precise Intersection 算子用于计算高斯球-像素块（tile）映射关系，基于 ［FlashGS 算法］(https://arxiv.org/abs/2408.07967)实现。”分别给出双端正文事实；算法卡把光栅化组织为自研算子流水，Precise Intersection 卡负责投影后生成高斯球到 tile 的命中映射，连接整体算法与排序前的空间筛选阶段。
- [GaussianSort —— 3DGS tile 内高斯球深度排序算子](gaussian_sort.md)（`related`）：“`flash_gaussian_build_mask(...)`（［precise-intersection］(precise_intersection.md)）输出 `tile_sums / tile_offsets / tile_depths / tile_gauss_ids`。”；“- 输出：`tile_sum`（每 tile 命中高斯数）、`tile_depths`（排序用深度）、`gauss_index`（命中高斯球 ID）。”。Precise Intersection 生产 GaussianSort 所需的 tile 计数、深度和高斯 ID。
- [Projection-3DGS —— 3D→2D 高斯球投影融合算子（前向/反向）](projection_3dgs.md)（`related`）：“- 上游：［projection-3dgs］(projection_3dgs.md)（提供 2D 投影属性）；下游：［gaussian-sort］(gaussian_sort.md)、［calc-render］(calc_render.md)”与“- 下游：［precise-intersection］(precise_intersection.md)（消费本算子产出的 2D 投影属性 means2d/conics/covars2d 算高斯-tile 精确相交）”提供双方正文证据。双方正文明确给出 projection 的 means2d、conics、covars2d 是 precise-intersection 的上游输入，构成 3DGS 光栅流水的生产者到消费者边。
<!-- cannbot:related:end -->
