---
type: Optimization
title: "X29: Shift-Free Tap-Comb 稠密直算（stride=1 反卷积消 Gather）"
description: "对 stride==1 的反卷积/ConvTranspose2d，利用数学恒等变换把转置卷积化为零填充输入 + 180° 翻核的标准 cross-correlation，再用 shift-free tap-comb 稠密 Axpy 取代逐 tap Gather 与 col2im 散射。"
tags:
  - task.optimization
  - topic.compute.neighborhood.convolution
  - topic.data_movement.layout_transform
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X29: Shift-Free Tap-Comb 稠密直算（stride=1 反卷积消 Gather）

## 核心思路

对 stride==1 的反卷积/ConvTranspose2d，利用数学恒等变换：
**ConvTranspose2d(x, w, stride=1, pad) ≡ 零填充输入 + 180° 翻核的标准 cross-correlation**：
`out[co,oh,ow] = bias[co] + Σ_{ci,kf,kf2} wf[ci,co,kf,kf2] * P[ci,oh+kf,ow+kf2]`
其中 `P[ci] = x[n,ci]` 上下左右各补 `t = KH-1-pad` 个零，`wf[kf][kf2] = at[...,(KH-1-kf)*KW+(KW-1-kf2)]`（翻核）。

单 kernel（Direct-AIV）内实现 **shift-free tap-comb**：
- 每 (ci,kf2) 构造 `comb[ci][kf2][row][0:woA] = P[ci][row]` 左移 kf2 的对齐槽（8-float=32B 对齐）；
- 固定 (ci,kf2,kf) 时 comb 中 `kf..kf+ho-1` 行 CONTIGUOUS，因此每 (ci,kf2,kf,co) 的累加是**一次对齐 Axpy(len=ho*woA)**；
- 稠密 Axpy 链取代逐 tap 的 Gather 间接寻址，**彻底消除 Gather/col2im 散射/G workspace 往返/AIC→AIV 交接**。

相比 Gather-based 直接累加，X29 的 shift-free 布局让 V-pipe 仅做对齐稠密 FMA。

## 适用场景

- 小 ci、stride=1 的 ConvTranspose2d / deconv（固定开销/交接主导，Gather 爆炸受限）
- 判定特征：`Gather 指令多 + 单 kernel 化可消除 AIC→AIV 交接 + ci 小（工作集 < UB）`
- host 按 stride 分发：stride==1 走 dense，非 stride-1 / 大 UB 回退 cube GEMM + col2im

## 实现要点

- **零填充平面尺寸必须 `ph = ho+kh-1`（不是 `hi+2t`）**：pad>0 时后者少一行，comb 读取越界。
- **DataCopyPad UB→GM blockLen 必须 ≥ 32B**：wo<8 时更小的 blockLen 直接 507015 ADDR_MISALIGN（GM→UB 方向无此限制）。规避：host 分配 `[n][co][ho][woA]` 填充缓冲，kernel 单次 bulk DataCopyPad 写，host 返回 `[:wo]` 视图。
- **DataCopyPad(GM→UB)+left/rightPadding 向量化 comb 构建在 dav-2201 上 507015 fault**：回退标量 SetValue（残余标量 comb 放置）。
- **host 预处理下沉**：host 不再构造预填充张量（permute/reshape/zeros/copy），直接传原始 NCHW x；kernel 按 x[n][ci] 连续平面 blockCount=1 DataCopyPad 读取。
- 权重预翻核：`wf[kf][kf2]=at[...,(KH-1-kf)*KW+(KW-1-kf2)]` 在 host 预计算或 kernel 标量预翻核。
- 残余开销：标量 comb 放置 + 稠密 Axpy 链 + 单 kernel launch 地板。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带；布局变换类改动需覆盖 pad/stride 边界与原始 NCHW 输入路径。
