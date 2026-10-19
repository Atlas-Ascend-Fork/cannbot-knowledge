---
type: Optimization
title: "X94: 可分离重采样/插值的 Gather 提升（逐输出行 4 次 Gather → 每输入行 2 次）+ 取消列块循环 + 输入读一次"
description: "原始数据流每输出元素算out = hl0·(w0·gA + w1·gB) + hl1·(w0·gC + w1·gD) → 4 次 Gather + 9 条向量算子，且外层按输出列块（ncb = ceil(WO/ctile)）循环，每个列块重搬整行输入 ⇒ 输入读放大 2·ncb 倍/输出行。"
tags:
  - task.optimization
  - topic.memory
  - topic.programming_model.execution_unit.vector
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# X94: 可分离重采样/插值的 Gather 提升 + 取消列块循环

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X94
> title: "X94: 可分离重采样/插值的 Gather 提升（逐输出行 4 次 Gather → 每输入行 2 次）+ 取消列块循环 + 输入读一次"
> origin: discovered
> discovered_round: 1
> discovered_from: "14_resize_bilinear evolution round_1/parallel_2 (x0, open_exploration) 与 round_1/parallel_0 (n2, workflow_guided) 独立收敛到同一数据流"
> base_speedup: "同 10 例子集 core 比值 3.4202 → 0.6153/0.6280；全量 50 例 core 比值 0.5122（相对基线生成核 6.01x）"
> confidence: single_op
> status: active
> op_families: [cv_fusion, pooling_gather, index_scatter, elementwise]
> bottlenecks: [mte2_stall, scalar_compute, partial_overlap, undersize_transfer]
> tags: [resize, interpolate, bilinear, upsample, separable, gather-hoisting, ring-cache, column-block-elimination, read-once, 910b2c, dav-c220, pure-vector]
> strategy_ids: [X94, X29, X70, X93, P33, P97, P56, P66]
> ```

**Source**: 14_resize_bilinear evolution, round_1 —— `parallel_2`（x0, open_exploration，未读策略库）与
`parallel_0`（n2, workflow_guided）**两条独立线收敛到同一数据流**，互为独立复现。
**Speedup**: 同 10 例 in-loop 子集 core 比值 3.4202 → 0.6153（n2）/ 0.6280（x0）；
全量 50 例最终验收 core 比值 **0.5122**（n=50，min 0.2841 / max 1.0590），
相对基线生成核 **6.01x**；50/50 精度 PASS（全量 `evaluate_ascendc.sh`，逐例 MERE 与重构前
bit-identical，说明只改「怎么算」不改「算什么」）。
**Operator type**: NCHW 双线性重采样（`F.interpolate(mode='bilinear')`），二维 2-tap 可分离滑窗 + 运行时索引 gather，纯向量内核。
**Hardware**: Ascend910B2C (DAV_2201 / dav-c220)

## 核心思路

原始数据流每**输出元素**算
`out = hl0·(w0·gA + w1·gB) + hl1·(w0·gC + w1·gD)` → **4 次 Gather + 9 条向量算子**，
且外层按输出列块（`ncb = ceil(WO/ctile)`）循环，每个列块重搬整行输入 ⇒ 输入读放大 `2·ncb` 倍/输出行。

利用**双线性可分离**：`Hor[h][j] := w0[j]·X[h][i0[j]] + w1[j]·X[h][i1[j]]` 只依赖
**（输入行号 h，输出列号 j）**，与输出行号无关；而原实现让每个输出行各自 gather 一次横向结果
（`scale=2` 时同一输入行被 4 个输出行各 gather 一遍）。改两趟：

1. **横向趟**：对每个**输入行**只做一次横向重采样 → `in_h` 行（宽 WO），**2 次 Gather/输入行**
   （Gather 总量 4·WO/输出行 → 2·WO/输入行 ≈ 1·WO/输出行，`scale=2` 时降 ~4x）；
2. **纵向趟**：`out = hl0·in_h[h1] + hl1·in_h[h2]`，**零 Gather**，纯向量 Mul/Add；
3. **中间量按输入行号打 tag 的环形缓存**（2-3 槽即够，见下「缓存尺寸」），保证每个输入行的横向趟
   **恰好执行一次**；
4. **列权/索引表按输出整宽 WO 一次物化**（`ctile = WO ⇒ ncb ≡ 1`），**列块循环整体消失**
   ⇒ 输入从 GM **只读一次**（原为 `2·ncb` 次/输出行）。

## 适用条件

- **可分离的两维/多维线性重采样**：双线性 resize、remap 的可分离特化、任何 `out = A·X·Bᵀ` 形式的
  线性重采样（A/B 为稀疏插值矩阵）。判据：`model.py`/kernel 里坐标与权重对两轴各自独立。
- **横向重采样结果与另一轴的行号无关**（这是提升成立的前提；若权重同时依赖双轴则必须先做别的分解）。
- 参考核是**设备侧 kernel**（本行为 CANN 内置 ResizeBilinearV2 / UpsampleBilinear2d），不是带宽极限：
  参考聚合带宽仅 362 GB/s、最好例 690 GB/s，本机实测峰值 1.2-1.4 TB/s ⇒ 有 1.25x 以上的空间。
- 想做「每输入行只读一次」时要求 UB 能放下 `3 × WO × sizeof(T)` 的滚动窗口
  （WO=4096 fp32 → 48KB，UB 192KB 可放；WO 更大时按列块切 in_h 槽或回退原结构）。

## 实现要点

- **先过 `_common-prerequisites.md` C1-C5**：C2（Gather/索引表逐元素搬运 → P33/P100）、
  C4（无真双缓冲 + 非 32B 对齐 → P1/P7）、C5（跨 pipe 依赖 → A4）在本算子全部命中。
- **列索引/权重表**（P33）：`offA/offB` 必须是**字节**偏移（OKF f28：`AscendC::Gather` 的 `srcOffset`
  单位是字节，原式 `oiA = wi·esz` 正确；换写法务必重新推导单位）。表只依赖输出列号 ⇒ 提到行循环外、
  每核一次。
- **表缓冲瘦身**：原实现按 ctile 开 16 张 float/int 表 + 5 个 T 缓冲；只需
  `offA/offB`（uint32 字节偏移）+ `w0l/wl`（float）4 张常驻，其余中转缓冲在行循环内复用
  （P8 UB 分区复用、P97 零拷贝子张量切片）。
- **同步纪律**：原码每输出行开头一条 `PipeBarrier<PIPE_ALL>` + 十余次 `PipeBarrier<PIPE_V>`，
  单行 ~25 次跨 pipe 同步把流水反复排空。改成**精确事件同步**：`V_MTE2` / `MTE2_V(按 staging 奇偶)`
  管输入行载入与 Gather 先后，`V_MTE3` / `MTE3_V` + 输出双缓冲管纵向结果与回写；
  平面切换/列块收尾要 drain 未消费的预取，保持事件计数平衡。
  ⚠ 不要一次删光屏障（OKF f21：一次删 100% 屏障会非确定性挂死），按依赖逐段放。
- **标量地址计算**：`tl_floormod/ tl_floordiv`（每行 2 次软件模拟 int64 除法）换成
  `(plane, oh)` **加法增量推进**，与除法逐位同值（本算子实测这一项单独 +19.6%）。
- **输入行顺序流式**：`roundup64(w)` 的 staging 环 + 「预取提前 1-2 行发起」让 MTE2 与 Gather 重叠。
- **精度纪律**：坐标与权重表的运算顺序**必须沿用原生成码逐位不动**
  （`align_corners=0` 分支的 `+0.5 → ×rw → −0.5 → max(0)` 不可提常量、不可改顺序），
  否则 fp32 逐位一致性会破。验收时逐例 MERE 应与重构前**完全相同**。
- **缓存尺寸**：`scale_h=2.0, align_corners=False` 时 out 行 2k 用 (h1,h2)=(k-1,k)、
  行 2k+1 用 (k,k+1) ⇒ 行 2k 的 `gC/gD` 恒等于行 2k+1 的 `gA/gB`，**2-3 槽 tag 环形缓存足够**；
  一般情形按「所需行号不在环内则重算并逐出最久未用」处理（h1/h2 单调不减，环只会前进）。

## 收益归因（本算子实测）

| 项 | 改前 | 改后 |
|---|---|---|
| Gather 元素/输出行 | `4·WO` | `≈1·WO`（scale=2） |
| 向量算子/输出元素 | 9 | `3/scale_h + 3` |
| 输入 GM 读/输出行 | `2·ncb` 行 | `1/scale_h` 行（读一次） |
| 每输出行 `PipeBarrier<PIPE_ALL>` | 1 | 0 |
| 列块循环 | `ncb` 次输入重载 + 表重算 | `ncb ≡ 1` |

## 边界 / 坑

- **瓶颈归因易被混淆**：Gather 元素数与 MTE 字节数都与「每输入行 W」成正比，用时长对
  「Gather 元素数」做回归会得出「Gather bound」的伪结论。必须用
  `--aic-metrics=PipeUtilization` 直接看 pipe 占比；且该表的 `aiv_<pipe>_ratio` 列在
  `--quick`（无 aic-metrics）路径上**分母不一致**（同一列在不同轮次时而按 40 AIV 求和时而不求和，
  本例同一算子出现过 `scalar 0.912/vec 0.047` 与 `vec 0.912/scalar 0.415` 并列），
  只能定性、不能定量。
- 本内核 AIC 分支无计算，但 `MIX_AIC_1_2` 会派发整波空转 AIC 并贡献
  `aic_mac_ratio 0.491 / aic_fixpipe_ratio 0.363 / aic_scalar_ratio 0.36-0.45` 的**自旋记账**；
  归因时须把这部分当噪声。OKF X75 提示改 `AIV_ONLY` 可消除，但 X93 记录该改动在**已带手工事件编排**
  的 kernel 上会挂死，必须独立同窗口 A/B，不可照搬。
- **小 case 地板**：改完后唯一 >0.8 的例是 `[1,16,94,256]`（比值 1.059，7.7MB 流量）——
  已被 launch/dispatch 地板支配，算法级优化对它无效，只能从派发/每核固定成本入手。
- 与 OKF X29（shift-free tap-comb，规则 stride 去 Gather）、X70（数据相关 gather 的指令削减）、
  X93（复制型上采样 = 本卡 `scale` 为整数、权重全 1 的退化特例）同族，可叠加。

## 来源

自动发现于 14_resize_bilinear 进化 round_1：`parallel_2`（x0, open_exploration）+ `parallel_0`（n2）。
全量 50 例验收：core 比值 geomean 0.5122（参考 = CANN 内置核的逐例 core 耗时），50/50 精度 PASS。
