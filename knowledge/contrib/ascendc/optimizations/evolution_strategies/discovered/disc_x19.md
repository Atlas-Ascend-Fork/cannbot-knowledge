---
type: Optimization
title: "X19: 1×1 Conv 翻转 GEMM（原始布局即操作数，免 wrepack/im2col）"
description: "1×1 卷积的 im2col 是恒等变换：NCHW 原始布局的 x 本身就是 [K=Ci, M=HW] 的 GEMM B 操作数，翻转 GEMM 后权重与输入均免重排，epilogue 按通道行写出 NCHW。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p130_1x1conv_flipped_gemm
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X19: 1×1 Conv 翻转 GEMM（原始布局即操作数，免 wrepack/im2col）

> **已晋升为 P130**：策略卡见 [../cards/p130_1x1conv_flipped_gemm.md](../cards/p130_1x1conv_flipped_gemm.md)，Playbook 见 [../../../runbooks/performance/p130_1x1conv_flipped_gemm.md](../../../runbooks/performance/p130_1x1conv_flipped_gemm.md)，precondition YAML 见 cannbot-skills 仓 `community/ops/ascendc-evolution-strategies/references/preconditions/`。本文件保留该策略的详细机制说明，卡片内容以 P130 为准。

## 核心思路
1×1 卷积的 im2col 是恒等变换：NCHW 原始布局的 x 本身就是 `[K=Ci, M=H*W]` 的
GEMM B 操作数。把 GEMM **翻转**——A = 原始权重 [Co, Ci]（跨图共享，免 wrepack）、
B = 原始 x [Ci, H*W]（免 im2col 发射）、acc = [Co, H*W] fp32——epilogue 按通道行
加 bias 后直接写出 NCHW，全程零 transpose、省两级 kernel 发射。

## 适用场景
- **算子类型**: 1×1 卷积（kH=kW=1、s=1、p=0、d=1），pointwise conv、1×1 reduction
- **瓶颈类型**: launch-bound / 小 kernel 发射开销占比大；或大 Ci 1×1 的
  im2col 纯搬运浪费
- **前提条件**: Ci%16==0（Nd2Nz 分形约束）且 (H*W)%16==0（B' 行 32B 对齐）。
  注意：用 UB 中转 pad 解除 (H*W)%16 门控是**净负收益**（xpad 走 DataCopyPad
  慢速 dummy-pad 路径，翻转 GEMM 在窄 padded 行上也更慢），门控不满足时回
  normal 路径，勿强解

## 实现要点
1. 全通路保持 Nd2Nz GM→L1（plain 2D DataCopy GM↔L1 在 dav-c220 不可靠）
2. 翻转后 m 维 = Co（通道）、n 维 = H*W（空间）：epilogue 的 acc 行为通道行，
   整块连续区域一次 load + 行内标量 Adds（V pipe 行间免同步）+ 一次 cast +
   一次 store，优于逐行 flag pair
3. 空间尾 n 维非 16 对齐时 LoadData3D Zn 的 channelSize 必须 round16，
   否则跳部分分形块导致列数据损坏
4. 与 X10 的模式分发组合：host 按几何判定走本模式还是 normal/fused

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
