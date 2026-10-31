---
type: Concept
title: CalcRender —— 3DGS Alpha-blending 渲染融合算子（前向/反向）
description: CalcRender 是 3DGS 光栅化的核心渲染算子，把空间中已排序的 3D 高斯球颜色 alpha-blending 到各像素上，构成对应视角的渲染图。host 定义为 CalcRenderFwdDoubleClipGsids（前向）与 CalcRenderBwdVarClipGsids（反向），由 rasterizer.py 中 calc_render(...) 调用。被 3d-gaussian-splatting 串联在渲染流程末端。
tags:
- task.implementation
- topic.rendering
- topic.compilation
- topic.three_dimensional_reconstruction
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/gaussian_splatting_alpha_blending_optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- a2
---

# CalcRender —— 3DGS Alpha-blending 渲染融合算子

`CalcRender` 是 3DGS 光栅化的核心渲染算子，把空间中已排序的 3D 高斯球颜色 alpha-blending 到各像素上，构成对应视角的渲染图。host 定义为 [`CalcRenderFwdDoubleClipGsids`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/kernels/op_host/calc_render_fwd_double_clip_gsids.cpp)（前向）与 [`CalcRenderBwdVarClipGsids`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/kernels/op_host/calc_render_bwd_var_clip_gsids.cpp)（反向），由 `rasterizer.py` 中 `calc_render(...)` 调用。被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联在渲染流程末端。

- 前向输入 `gs / tileCoords / offsets / gsIds`，输出 `color / depth / lastCumsum / error / gsClipIndex / alphaClipIndex`。
- 反向输入含 `vColor / vDepth / lastCumsum / error / gs / ... / gsClipIndex_gsIds / alphaClipIndex`，输出 `vGs`。
- 名称中的 `DoubleClip` 对应两级剪枝、`Gsids` 对应反向需要的终止高斯球 ID 记录。

## Alpha-blending 计算公式

$$ C = \sum_{i \in N} c_i \alpha_i \prod^{i-1}_{j=1}(1-\alpha_j) $$
$$ \alpha_i = o_i \exp(-\tfrac{1}{2} \delta^T \Sigma \delta) $$

整体流程：按 tile 对 vector core 切分，每核循环渲染分配到的 tile 上所有像素；因累乘存在，必须对高斯球排序后**依次渲染**（for 循环遍历每个高斯球）；对每个高斯球并行计算其对 tile 上所有像素的 alpha 与颜色贡献；逐像素更新累积颜色与透明度。

## SIMD 架构下的实现难点

1. **流水设计复杂**：高斯球间及单球内部计算有前后依赖，需插 PipeBarrier 保证正确性，流水效率低。
2. **访存与计算开销相互掩盖难**：高斯球数量多、单 tile 渲染的高斯球地址不连续，访存开销大。
3. **冗余计算**：每个高斯球都要对 tile 全部像素计算，存在大量冗余。

## 高斯球流水优化

### 指令流水并行

由 msprof op simulator 仿真：对 64 个 float 算 VMuls 需 15ns，而 2048 个 float 并非 32 倍，仅需 51ns（含指令解码与数据预取开销）。因此把**多个高斯球中无依赖的部分（α 计算）合并**以减少 PipeBarrier 频率：每次处理高斯球数提升到 **4 个**，处理完 4 个后再插一次 PipeBarrier。实现上把单球计算拆成两阶段——阶段一并行算 4 个球的 α 并暂存，阶段二再依次算颜色贡献并更新累积值；代价是 UB 占用增加，需仔细复用 UB（如颜色渲染时复用前一球 α 计算的空间）。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/pipeline.jpeg" width="70%">

<sub>4 高斯球合批流水图。来源：[alpha_blending 优化文档](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/gaussian_splatting_alpha_blending_optimization.md)。</sub>

### Double Buffer 优化

用 Double Buffer 在处理当前批高斯球的同时预读下一个高斯球属性到第二块 buffer，掩盖访存延迟。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/pingpong.jpeg" width="70%">

<sub>Ping-pong（Double Buffer）预读。来源同上 alpha_blending 文档。</sub>

## 两级高斯球剪枝

受 SIMD 连续地址计算限制，无法对单像素细粒度剪枝，故设计 tile 级 + sub-tile（像素行）级两级剪枝。

- **Tile 级剪枝**：累积透明度达阈值后后续高斯球贡献可忽略。每处理完一组（4 个）高斯球后做阈值检查：用 `CompareScalar` 把所有像素累积透明度与阈值比较生成掩码 → `ReinterpretCast` 转 64 位整数 → for 循环与 `UINT64_MAX` 按位与，全相等说明所有像素达阈值即可结束渲染。需记录每个 tile 终止渲染的高斯球 ID 供反向从该 ID 续算梯度。该级收益仅 5~10%（必须所有像素都满足才生效）。
- **Sub-Tile（像素行）级剪枝**：经评估单高斯球实际只影响约 6×6 像素，而 tilesize 为 32×32，故单球实际只覆盖约 20% 像素行。流程：算 α 与高斯球投影影响范围 → `WholeReduceMax` 取每像素行 α 最大值 → `CompareScalar` 与阈值比较生成掩码 → 掩码转 64 位整数后用 `ScalarCountLeadingZeros`（小端下首个 1 对应最后一个需渲染行）+ `ScalarGetCountOfValue<1>`（需渲染行数）确定渲染行范围。反向用 UInt8 在 UB 记录每球起止行，每 1024 球写回 GM。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/alpha_culling.jpeg" width="70%">

<sub>像素行级剪枝示意。来源同上 alpha_blending 文档。</sub>

## 负载均衡（贪心切分）

通用「按像素块均匀切分」无法感知各 tile 计算量，个别 core 因高斯球过多拖尾。采用贪心算法「**先重后轻，分给最轻**」：① 按 tile 对应高斯球数从大到小排序；② 依次把 tile 分给当前高斯球数最小的 vector 核。该调度由自研 C++ 算子 `GetRenderSchedule`（[`csrc/GetRenderSchedule.cpp`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/meta_gauss_render/csrc/GetRenderSchedule.cpp)，`std::sort` + 优先队列实现；Python 封装 [`ops/get_render_schedule.py`](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/ops/ascendc/meta_gauss_render/ops/get_render_schedule.py)）在 host 端计算，结果作为 `lb_sched` 喂给排序/渲染算子。

四块（高斯球 50/100/10/20）分 2 核的例子：均匀切分得 150/30（倾斜），负载均衡得 100/80。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/gaussian_tile_origin.png" width="45%"> <img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/gaussian_tile_segmentation_result.png" width="45%">

<sub>左：待分配 tile；右：均匀切分 vs 负载均衡对比。来源：[load_balance 优化文档](../../../../../cann-recipes-raw/cann-recipes-spatial-intelligence/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/gaussian_splatting_load_balance_optimization.md)。</sub>

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/tile_ngauss_sort.png" width="55%">

<sub>tile 按高斯球数降序排序。来源同上 load_balance 文档。</sub>

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/figure/gaussian_load_balance.png" width="70%">

<sub>贪心分配过程（core-0=100, core-1=80）。来源同上 load_balance 文档。</sub>

## 性能数据

含 13 万高斯球（过滤后 67917 个渲染）场景、30000 iters、α 阈值 0.004、不透明度阈值 0.99（device 耗时 ms）：

| 优化方法 | PSNR | 前向 | 反向 |
| --- | --- | --- | --- |
| 无优化 | 25.008 | 4.807 | 18.710 |
| 流水优化 | 25.005 | 4.379 | 17.565 |
| 剪枝优化 | 25.010 | 5.101 | 13.141 |
| 流水+剪枝 | 24.974 | 4.495 | 13.107 |

不同 α 阈值（仅评估未重训）：阈值越高对反向收益越明显，阈值 0.1 时反向降到 1.410 ms（约原 7.5%），PSNR 仅降 3.3%（25.082→24.274）。同一 13 万球场景（device 耗时 ms）：

| 阈值选取 | PSNR | 前向device耗时(ms) | 反向device耗时(ms) |
| -------- | -------------- | -------- | ------- |
| 0 | 25.082 | 4.379 | 18.710 |
| 0.004 | 25.009 | 4.495 | 13.107 |
| 0.01 | 24.949 | 4.358 | 11.267 |
| 0.02 | 24.872 | 4.236 | 9.827 |
| 0.05 | 24.672 | 4.130 | 7.937 |
| 0.1 | 24.274 | 3.539 | 1.410 |
| 0.2 | 23.309 | 3.764 | 1.043 |

<sub>α 阈值 vs PSNR/前向/反向 权衡。来源：[alpha_blending 优化文档 §不同 α 阈值对剪枝效果的影响](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/0d955a020eed3ac1f274e5ab26f792b02b011728/docs/algorithms/gaussian_splatting/gaussian_splatting_alpha_blending_optimization.md#不同alpha阈值对剪枝效果的影响)。</sub>

负载均衡 vs 按块切分：前向 5.973→4.599、反向 15.908→12.223（均约 23%）。

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 上游算子：[gaussian-sort](gaussian_sort.md)（渲染前按 tile 排序）、[precise-intersection](precise_intersection.md)（提供高斯球-tile 映射）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)
