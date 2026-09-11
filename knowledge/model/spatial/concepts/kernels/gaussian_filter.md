---
type: Concept
title: GaussianFilter —— 3DGS 视锥剔除融合算子（前向/反向 Scatter）
description: Culling（剔除）是渲染前的关键优化步骤：提前过滤对当前帧渲染无贡献的高斯球，减少后续投影/排序/Alpha-blending 计算量。GaussianFilter 把视锥剔除融合为单算子，host 定义见 gaussian_filter.cpp，在 projection_three_dims_gaussian_fused(...) 内与投影一同调用。被 3d-gaussian-splatting 串联。
tags:
- task.implementation
- topic.rendering
- topic.compilation
- topic.three_dimensional_reconstruction
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_culling_optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-06-13T00:00:00Z'
platforms:
- a2
---

# GaussianFilter —— 3DGS 视锥剔除融合算子

Culling（剔除）是渲染前的关键优化步骤：提前过滤对当前帧渲染无贡献的高斯球，减少后续投影/排序/Alpha-blending 计算量。`GaussianFilter` 把视锥剔除融合为单算子，host 定义见 [`gaussian_filter.cpp`](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/ops/ascendc/kernels/op_host/gaussian_filter.cpp)，在 `projection_three_dims_gaussian_fused(...)` 内与投影一同调用。被 [3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md) 串联。

- 输入：`means / colors / det / opacities / means2d / depths / radius / conics / covars2d / compensations`；属性 `width / height / near_plane / far_plane`。
- 输出：各属性的 `*_culling`（过滤后紧凑数组）+ `filter`（比特掩码，位=1 表示有效）+ `cnt`（有效计数）。

## 视锥剔除逻辑

只保留「当前相机能看到」的高斯球，丢弃看不到的：
- **无效高斯剔除**：确保高斯是合法正定矩阵（非退化、非扁平）。
- **深度方向**：剔除深度 < 近裁切面或 > 远裁切面（`near_plane`/`far_plane`）的高斯。
- **水平/垂直方向**：剔除投影 2D 椭圆 x/y 半径为 0 的高斯。
- **屏幕外剔除**：仅保留投影椭圆与屏幕有重叠的高斯。

## 实现难点

- **比特位-元素映射对齐**：`filter` 为 uint8，每元素存 8 个高斯的掩码状态，核内迭代时输入分片必须是 **8 的整数倍**，否则比特位跨元素映射错乱。
- **核间数据依赖**：切分涉及核间依赖，必须引入全局同步（`SyncAll`），但同步有开销，需在保精度前提下减少同步次数。
- **反向 Scatter**：把过滤后数据分散还原到原始位置，难点在对无规则 `filter` 构建 `GatherMask` 的分散索引。

## Tiling 分核

高斯数普遍十万以上，故不对 batchsize/相机数分核，只对**高斯**分核。要点：`filter` 为 uint8 需对头核做 8 元素对齐；对齐后尾核可能算出负数，需反推实际使用核数再算尾核。设核数 `coreNum`、总数 `N`：

$$ perCoreN = \lceil \lceil N/coreNum \rceil / 8 \rceil \cdot 8 $$
$$ usedCoreNum = \lceil N/perCoreN \rceil $$
$$ lastCoreN = N - usedCoreNum \cdot perCoreN $$

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/gaussian_filter_tiling.png" width="70%">

<sub>tiling 分核（8 元素对齐 + 尾核反推）。来源：[culling 优化文档](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/gaussian_splatting_culling_optimization.md)。</sub>

## 前向 kernel：两阶段 + 偏移计算

因 UB 大小限制，单核一次迭代无法过滤出所有有效高斯，故需累积偏移。设第 $i$ 核有效高斯 $cntPerCore_i$、第 $i$ 核第 $j$ 次迭代有效高斯 $cntPerCore_{i,j}$，则搬出偏移：

$$ offset = \sum_{k=0}^{i-1}{cntPerCore_k} + \sum_{k=0}^{j-1}{cntPerCore_{i,k}} $$

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/gaussian_filter_kernel.png" width="70%">

<sub>kernel 搬运偏移示例。来源同上 culling 文档。</sub>

第 $i$ 核偏移依赖 0…$i-1$ 核结果，而各核同步计算，无法一次算出，故用 `SyncAll` 分两阶段：

- **Phase1**：执行 $loopN$ 次迭代完成 `filter` 搬入/计算/搬出，统计核内累积 `cntPerLoop`、更新 `cntPerCore`，存入 `workspace` 后 `SyncAll` 全局同步；随后更新并迁出 GM 上的 `coreOffset`，仅最后一个核执行全局计数汇总并迁出。
- **Phase2**：重新搬入 `filter`，再执行 $loopN$ 次迭代，以 `filter` 为 mask 用 `GatherMask` 执行剔除，结合 `coreOffset` 与 `cntPerLoop` 确定全局内存偏移；用 3 个 `TQue` 让 MTE2/Vector/MTE3 流水并行。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/gaussian_filter_kernel_p1.png" width="70%">

<sub>Phase1 示意。来源同上 culling 文档。</sub>

## 反向梯度还原（Scatter）

反向需把过滤后数据恢复到原位（数据分散）。为避免循环+标量计算的长耗时，用 `GatherMask` + `Sort` + `Gather` 多 API 结合：

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/scatter_purpose.jpeg" width="65%">

<sub>Scatter 目标：过滤后数据回原位。来源同上 culling 文档。</sub>

- **Phase1（构建新索引）**：构造等长元素索引 `Index`(0,1,…,`cntPerLoop`)；用 `GatherMask` 对 `filter` 位为 1 的元素收集 `Index` 存入 `headIndexTensor`，位为 0 的存 `tailIndexTensor`，拼接得 `newIndex`。Tensor 操作需 32 字节对齐，拼接时先把两部分拷到 GM 连续地址再拷回 UB。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/index_concat.jpeg" width="65%">

<sub>newIndex 拼接。来源同上 culling 文档。</sub>

- **Phase2（排序 + Gather 重排）**：`Sort` 对 `newIndex` 排序得排序值 `score` 及原位置索引；用 `Extract` 分离索引（即 `Gather` 取元素的地址偏移）。因 `Sort` 仅支持降序，需构造等差数列对 `Extract` 索引重排得升序。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/gather_newindex.jpeg" width="65%">

<sub>Extract 得到 Gather 索引。来源同上 culling 文档。</sub>

## 数据搬运优化（Transpose 替代构造 index）

数据在 `LocalTensor` 按 N 维切分，计算时为方便 vector 运算把高斯球维放到 Tensor 最后；输出需还原 shape（交换最后一维与倒数第二维）。以 `(B,3,N)`→`(B,N,3)` 为例，原本要构造形如 `[0, perLoopN, perLoopN*2, 1, ...]` 的 index 再 `GatherMask`，构建 index 需大量 Scalar 运算性能差。改用 `Transpose` 接口搬运替代构造 index。

<img src="https://raw.gitcode.com/cann/cann-recipes-spatial-intelligence/raw/92747ee512faebff6068704f893d19d622f7282a/docs/algorithms/gaussian_splatting/figure/transpose.jpeg" width="65%">

<sub>Transpose 搬运优化。来源同上 culling 文档。</sub>

> 注：与 `GaussianFilter` 配套的投影反向算子 `FullyFusedProjectionBwd` 在计算前先做反视锥剔除还原原始 Tensor，无效高斯梯度自然置 0（见 [projection-3dgs](projection_3dgs.md)）。

## 相关页面

- 枢纽：[3d-gaussian-splatting](../algorithms/3d_gaussian_splatting.md)
- 配套：[projection-3dgs](projection_3dgs.md)（投影 + 反视锥还原）
- 跨域：[ascendc](../../../inference/concepts/frameworks/ascendc.md)