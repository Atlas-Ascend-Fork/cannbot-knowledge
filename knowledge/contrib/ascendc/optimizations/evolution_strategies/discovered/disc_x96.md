---
type: Optimization
title: "X96: 卷积归约轴的单维递延（kd-defer）——把 im2col 的展开维从 k² 降到 k，用 panel 对齐的 B 平移读把递延维恢复"
description: "卷积 im2col 物化的 col 行数按 k² 展开，其中 kd 维可由 m 索引平移重建。把 GEMM 归约轴从 (ci,kd,kh) 改为 (ci,kh)，kd 的 k 个 tap 由 cube 用 k 次 panel 对齐的 B 平移读恢复，可把 col 写侧与写后读侧同时降到约 1/k。前提是 W 轴无归约且 D 行距按 COL_PANEL 对齐。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X96: 归约轴单维递延（kd-defer）

## 判定信号

conv3d（或任何 `kernel_size=(k,k,1)` 型）的 im2col **物化**路径：`col` 的行数是 `Ci*kd*kh`，
而其中 **kd 那一维是靠 m 索引平移就能重建的冗余维** —— 只要 W 轴没有归约（`kW==1`），就有恒等式

```
col[(ci,kd,kh), m(n,do,ho,wo)] = xp[ci, do+kd*DL, ho+kh*DL, wo]
                               = col[(ci,0,kh), m(n, do+kd*DL, ho, wo)]
```

即「同一个 `col` 的不同 m 窗口」。判据：**`col` 的 DRAM 流量（写+读）占算法总流量的一半以上，
且 `col` 的行数按 k² 展开**；同时 W 轴是逐点映射（kW==1）。

## 核心思路

把 GEMM 的归约轴从 `(ci,kd,kh)` 改成 `(ci,kh)`（行数降 k 倍），kd 的 k 个 tap 由 cube 用
**k 次 panel 对齐的 B 平移读**恢复。代价是 cube 多读 k 次 `col_h`（读量基本持平，
因为 `col_h` 的列也扩到整个 padded D 范围 `DoExt = Do+(k-1)*DL`），
收益是 **col 的写侧与写后读侧同时降到 ~1/k**。

**全部技巧在「panel 对齐」这四个字上**：cube 的 B 读是 Nd2Nz 的 `(TK x TN)` 稠密块，
要求 `(m0+shift) % COL_PANEL + TN <= COL_PANEL`，即 **shift 必须是 COL_PANEL 的整数倍**。
做法：取 **D 行距按 COL_PANEL 对齐**，`HopPitch = RoundUp(Ho*Wpitch, COL_PANEL)`，则每个 kd 的平移
`(kd*DL)*HopPitch` 自动是 COL_PANEL 的整数倍，panel 结构不被破坏、Nd2Nz 的 dense-tile 前提保持。
再配一个 **D 晕圈** `DoExt = Do + (k-1)*DL`：`col_h` 的 d 轴覆盖整个 padded D 范围，
因此每个 kd 都能在 `col_h` 内取到自己的窗口。

## 实现要点

1. **恒等式的适用前提**：`kW==1`（W 轴无归约）。若 kW>1，需先做 W 轴的 tap 分解（可与 X90 的
   块对角打包叠加），否则平移读不成立。
2. **panel 对齐是硬前提**：`HopPitch` 必须是 `COL_PANEL` 的整数倍；`perN % COL_PANEL == 0` 的例满足。
   不满足的例必须**回退到原路径**，否则 Nd2Nz 会**静默积错列**。
3. **A 操作数要重打包**：host 按 `(kd, (ci,kh))` 序重排 `wp`（与块对角打包同一个循环），
   bias 行/ones 行折进 kd=0 那一块。
4. **数值**：累加顺序改变 ⇒ 逐例 maxdiff 会变；tol 1e-3 仍要求过，并给全量精度证据。
5. **与 X95（块数 KPI）正交**：本卡降的是**字节（写侧）**，同时也要按块数账核对；
   两者可叠加（X95 的基座先做块数削减，再叠本卡的轴递延）。

## 同族的第二条轴重构（可叠加）

把 **W 轴的 padding 从 m 轴消除**
（`m=((n·Do+do)·Ho+ho)·Wpitch+q`，q 只走**有效列集** `[P,P+W)`；S≥2 时 `[ceil(P/S), floor((P+W-1)/S)]`），
于是 im2col 直接读 `x`（连续多块、无 pad）、`xp` 整个删除、prepare 只剩 col 的 K-pad/ones 行与
bias-only 输出列的填充。注意这与「把 pad 搬进 im2col（DataCopyPad left/rightPadding）」**不是一回事**：
后者会让每个 feature-map 行多一个 DMA block，而 im2col 每 `(n,ci)` 要把平面 stage `kd` 次 ⇒
pad 读取被放大约 kd 倍 ⇒ **要消除、不要搬迁**。

## 边界 / 否定项

- `HopPitch` 不是 `COL_PANEL` 整数倍的形状**不能**用本卡（会静默积错列）；退回原路径。
- kW>1 的滑窗不满足恒等式，需先做 W 轴 tap 分解。
- 只降写侧；读侧若本来就一次读满（无复用），总 DRAM 流量的下降幅度约等于写侧占比。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 轴重排类改动额外覆盖 `HopPitch` 对齐与不对齐两类形状，并确认不对齐路径确实回退且无静默错列。
