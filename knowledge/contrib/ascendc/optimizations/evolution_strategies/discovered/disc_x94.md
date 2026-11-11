---
type: Optimization
title: "X94: 可分离重采样/插值的 Gather 提升（逐输出行 4 次 Gather → 每输入行 2 次）+ 取消列块循环 + 输入读一次"
description: "可分离双线性重采样按输出行重复做横向 Gather，且按列块循环重搬整行输入。利用双线性可分离性，把横向重采样提升到每个输入行只做一次（4 次 Gather → 2 次/输入行），纵向趟零 Gather，并用按输入行号打 tag 的环形缓存与列块消除做到输入只读一次。"
tags:
  - task.optimization
  - topic.memory
  - topic.programming_model.execution_unit.vector
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X94: 可分离重采样/插值的 Gather 提升 + 取消列块循环

## 核心思路

原始数据流每**输出元素**算
`out = hl0·(w0·gA + w1·gB) + hl1·(w0·gC + w1·gD)` → **4 次 Gather + 9 条向量算子**，
且外层按输出列块（`ncb = ceil(WO/ctile)`）循环，每个列块重搬整行输入 ⇒ 输入读放大 `2·ncb` 倍/输出行。

利用**双线性可分离**：`Hor[h][j] := w0[j]·X[h][i0[j]] + w1[j]·X[h][i1[j]]` 只依赖
**（输入行号 h，输出列号 j）**，与输出行号无关；而原实现让每个输出行各自 gather 一次横向结果
（整数倍缩放时同一输入行被多个输出行各 gather 一遍）。改两趟：

1. **横向趟**：对每个**输入行**只做一次横向重采样 → `in_h` 行（宽 WO），**2 次 Gather/输入行**
   （Gather 总量 4·WO/输出行 → 2·WO/输入行 ≈ 1·WO/输出行）；
2. **纵向趟**：`out = hl0·in_h[h1] + hl1·in_h[h2]`，**零 Gather**，纯向量 Mul/Add；
3. **中间量按输入行号打 tag 的环形缓存**（2-3 槽即够，见下「缓存尺寸」），保证每个输入行的横向趟
   **恰好执行一次**；
4. **列权/索引表按输出整宽 WO 一次物化**（`ctile = WO ⇒ ncb ≡ 1`），**列块循环整体消失**
   ⇒ 输入从 GM **只读一次**（原为 `2·ncb` 次/输出行）。

## 适用条件

- **可分离的两维/多维线性重采样**：双线性 resize、remap 的可分离特化、任何 `out = A·X·Bᵀ` 形式的
  线性重采样（A/B 为稀疏插值矩阵）。判据：坐标与权重对两轴各自独立。
- **横向重采样结果与另一轴的行号无关**（这是提升成立的前提；若权重同时依赖双轴则必须先做别的分解）。
- 参考核是**设备侧 kernel**（如 CANN 内置 ResizeBilinearV2 / UpsampleBilinear2d），不是带宽极限：
  若参考已接近峰值带宽，本卡空间有限。
- 想做「每输入行只读一次」时要求 UB 能放下 `3 × WO × sizeof(T)` 的滚动窗口
  （UB 192KB 为预算上限；WO 更大时按列块切 in_h 槽或回退原结构）。

## 实现要点

- **先过通用前置检查**：Gather/索引表逐元素搬运（P33/P100）、无真双缓冲 + 非 32B 对齐（P1/P7）、
  跨 pipe 依赖（A4）在本形态全部命中。
- **列索引/权重表**（P33）：`offA/offB` 必须是**字节**偏移（`AscendC::Gather` 的 `srcOffset`
  单位是字节；换写法务必重新推导单位）。表只依赖输出列号 ⇒ 提到行循环外、每核一次。
- **表缓冲瘦身**：原实现按 ctile 开多张 float/int 表与 T 缓冲；只需
  `offA/offB`（uint32 字节偏移）+ `w0l/wl`（float）4 张常驻，其余中转缓冲在行循环内复用
  （P8 UB 分区复用、P97 零拷贝子张量切片）。
- **同步纪律**：原码每输出行开头一条 `PipeBarrier<PIPE_ALL>` + 十余次 `PipeBarrier<PIPE_V>`，
  单行多次跨 pipe 同步把流水反复排空。改成**精确事件同步**：`V_MTE2` / `MTE2_V`（按 staging 奇偶）
  管输入行载入与 Gather 先后，`V_MTE3` / `MTE3_V` + 输出双缓冲管纵向结果与回写；
  平面切换/列块收尾要 drain 未消费的预取，保持事件计数平衡。
  ⚠ 不要一次删光所有屏障（会非确定性挂死），按依赖逐段放。
- **标量地址计算**：`tl_floormod / tl_floordiv`（每行软件模拟 int64 除法）换成
  `(plane, oh)` **加法增量推进**，与除法逐位同值。
- **输入行顺序流式**：`roundup64(w)` 的 staging 环 + 「预取提前 1-2 行发起」让 MTE2 与 Gather 重叠。
- **精度纪律**：坐标与权重表的运算顺序**必须沿用原生成码逐位不动**
  （`align_corners=0` 分支的 `+0.5 → ×rw → −0.5 → max(0)` 不可提常量、不可改顺序），
  否则 fp32 逐位一致性会破。验收时逐例 MERE 应与重构前**完全相同**。
- **缓存尺寸**：例如 `scale_h=2.0, align_corners=False` 时 out 行 2k 用 (h1,h2)=(k-1,k)、
  行 2k+1 用 (k,k+1) ⇒ 行 2k 的 `gC/gD` 恒等于行 2k+1 的 `gA/gB`，**2-3 槽 tag 环形缓存足够**；
  一般情形按「所需行号不在环内则重算并逐出最久未用」处理（h1/h2 单调不减，环只会前进）。

## 结构性对比

- Gather 元素/输出行：`4·WO` → `≈1·WO`（整数倍缩放）。
- 向量算子/输出元素：9 → `3/scale_h + 3`。
- 输入 GM 读/输出行：`2·ncb` 行 → `1/scale_h` 行（读一次）。
- 每输出行 `PipeBarrier<PIPE_ALL>`：1 → 0。
- 列块循环：`ncb` 次输入重载 + 表重算 → `ncb ≡ 1`。

## 边界 / 坑

- **瓶颈归因易被混淆**：Gather 元素数与 MTE 字节数都与「每输入行 W」成正比，用时长对
  「Gather 元素数」做回归会得出「Gather bound」的伪结论。必须用
  `--aic-metrics=PipeUtilization` 直接看 pipe 占比；且该表的 `aiv_<pipe>_ratio` 列在
  `--quick`（无 aic-metrics）路径上**分母不一致**，只能定性、不能定量。
- 本内核 AIC 分支无计算，但 `MIX_AIC_1_2` 会派发整波空转 AIC 并产生自旋记账；
  归因时须把这部分当噪声。X75 提示改 `AIV_ONLY` 可消除，但 X93 记录该改动在**已带手工事件编排**
  的 kernel 上会挂死，必须独立同窗口 A/B，不可照搬。
- **小形状地板**：改完后偏慢的例通常已被 launch/dispatch 地板支配，算法级优化对它无效，
  只能从派发/每核固定成本入手。
- 与 X29（shift-free tap-comb，规则 stride 去 Gather）、X70（数据相关 gather 的指令削减）、
  X93（复制型上采样 = 本卡 `scale` 为整数、权重全 1 的退化特例）同族，可叠加。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 重采样类改动额外覆盖整数倍/非整数倍缩放、`align_corners` 两支与 WO 超过 UB 滚动窗口的场景。
