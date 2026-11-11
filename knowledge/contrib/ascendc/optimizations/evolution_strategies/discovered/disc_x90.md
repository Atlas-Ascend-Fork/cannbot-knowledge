---
type: Optimization
title: "X90: 卷积/分组 GEMM 的归约轴 group-flatten（块对角权重打包）—— 消除按 group 重复的 K/co padding"
description: "卷积/分组 GEMM 中，若 col/acc 等 workspace 的 K 与 co padding 按 group 各付一次，搬运量会远大于 x+y。把 group 折进归约轴 K、权重在 host 侧打包为块对角矩阵，可让 padding 只付一次；配套变长 K panel、bias 折入惰性 ones 行、col 定点写零与条件式 Fixpipe 直写。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.reduction
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X90: 归约轴 group-flatten（块对角权重打包）

## 判定信号

读 profiling 的 `task_time` 时看到 **col/acc 一类 workspace 搬运量远大于 x+y 的字节数**，且 host tiling 里
出现 `RoundUp(..., 128)`（或任何大粒度对齐）**在 group/batch 维内侧**。此时
col = (G, KS=RoundUp(cig·k·k+1,128), M)、acc = (G, NS=RoundUp(cog,128), M)，
于是 **K 与 co 的 128 对齐 padding 各付 G 次**。

## 核心思路

**把 group 折进归约轴 K，权重在 host 侧打包成 (NS, KS) 的块对角矩阵**，让 K/co 的 padding 只付一次：

```
Kflat = Ci·k·k                        (ci 用**全局**通道号)
KS    = RoundUp(Kflat + 1, 16)        (N 维对齐粒度从 128 降到 16；+1 行留给 bias，见下)
NS    = RoundUp(Co, 128)
wp[co, k] = w[co_local, ci_local, kd, kh]   当 k = (g·cig + ci_local)·k·k + tap 且 co ∈ 本组行区间
          = 0                                否则（跨组项显式为 0）
```

数值等价：对 co ∈ 第 g 组，只有该组 K 列上的权重非零；其它列上的 col 是**有限**值 ⇒ `0 × finite = 0`，
累加分组变了但结果不变（maxdiff 为舍入量级，判据 1e-3）。

## 配套四项（缺一不可，否则 padding 只是搬了地方）

1. **K 去 padding + 变长 K panel**：`kPanel = min(TK, KS - kk·TK)`，panel 的
   `ndA.dValue / ndB.nValue / dstNzC0Stride / ldA.channelSize+kExtension / ldB.l1W+mExtension / mm.k`
   **全部随 kPanel 走**（K_ALIGN=16 保证每个 panel 都是整数个 fp32 C0(8) 块与 16 行 L1 fractal）。
2. **bias 折入惰性 ones 行**：host 写 `wp[co, Kflat] = bias[co]`，prepare 把 col 第 Kflat 行写成 1.0
   ⇒ bias 由 cube 在**累加内**免费加上。epilogue 的整条 bias 通路（bpad 张量 / per-co 标量 GetValue / Adds / 额外 PIPE_V）整体删除。
   —— 这一行原本在基线里是「惰性 ones 行」（权重列恒 0），把它改成 bias 列即零成本转正。
3. **col = at::empty + 定点写零**：prepare 按 m-panel 整块连续写 `rows [Kflat, KS)`（一行 1.0、其余 0.0，UB 只占 ≤16×128 fp32）。
   **关键约束**：这些行必须写**有限**值 —— fp32 mmad 里 `0 × NaN = NaN` 会污染 acc，所以不能只靠 `at::empty` 白嫖。
4. **条件式 Fixpipe 直写 y（X43 的窄门控形态）**：当 `Ws == Wo && Do·Ho·Wo % 128 == 0 && Co % 16 == 0` 时，
   `fp.dstStride = N·perN`、tile 基址 = `n·outCo·perN + n0·perN + r`，acc **不分配**、epilogue kernel **不发射**（三条流 → 一条）。

## 关键坑

1. **padding 按 group 付钱的三角关系**：只做 Kflat 而不做 `KS→RoundUp(...,16)` 与 `NS→RoundUp(Co,128)`，收益会大幅缩水；
   只做两者而不删「+1 ones 行」，那行仍是纯流量。
2. **`at::empty` 的 NaN 传染**：未被写入的行若是 garbage NaN/Inf，`0 × NaN = NaN` 直接毁掉 acc。必须逐区域审计并定点写有限值。
3. **UB→GM 多块 DataCopyPad 的源端按 blockLen 前进**：`blockCount` 必须夹到 `UB_FLOATS / tailElems`，否则 MTE 读 UB 越界
   （`The read address of the MTE instruction is out of range`）。
4. **Fixpipe 直写的 m-tile 必须与输出行对齐**（`%128 == 0` 且 `Ws == Wo`），否则 128 宽的 m tile 会跨 (n,do,ho) 行块或吃到 pad 列。
5. **隐式 im2col 的诱惑**：想进一步把 im2col 折进 GEMM 时先算账 —— xp 上各 tap 的行距不均匀
   （ci: `Dp·Hp·Ws`、kd: `Hp·Ws`、kh: `Ws`），单次 Nd2Nz 表达不了；拆成每 (ci,kd) 一次会让 DMA 调用数急剧上升，
   代价高于 im2col 物化本身。**该形态上隐式 im2col 通常是负收益**。

## 边界

- 适用前提是 **分组/批维上的 padding 放大明显**（即 G ≥ 2 或 Co 远小于对齐粒度）；G=1 且 Co 已对齐时本卡退化为仅 (2)(3)(4) 三项。
- 块对角权重使 wp 的行数从 `G·RoundUp(cog,128)` 降到 `RoundUp(Co,128)`：**G 越大收益越大**。
- mmad 的 task 数会随 NS 下降而下降，需复核多核均衡是否仍够。
- 若下游 epilogue 依赖 `acc` 的 `(G, cog, m)` 形状，要先把它改成 `(Co, m)` 再用本卡。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 权重打包类改动额外核对每个 group 的块对角边界、bias 行与 col 的有限值填充，并覆盖 G=1 与 G>1 两种形状。
