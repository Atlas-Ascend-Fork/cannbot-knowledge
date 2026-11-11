---
type: Optimization
title: "X57: attn+outproj 单 kernel 链融合 + native proj BLOCK_M 64 头合并 GEMM"
description: "MIX attention（AIC QK^T/PV + AIV softmax）与输出投影是两个串行 kernel，中间物化 [padM,Dp] attn GM workspace 并多一次 launch。融合为单 kernel：Phase 1 写 attn，`SyncAll<true>` GM grid barrier 分隔，Phase 2 AIC outproj 直接读 attn 写 out，L0A/L0B/L0C 两阶段共享；native proj 用 BLOCK_M 64 头合并 GEMM 提升 cube 利用率。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X57: attn+outproj 单 kernel 链融合 + native proj BLOCK_M 64 头合并 GEMM

## 核心思路
MIX attention（AIC QK^T/PV + AIV softmax）与输出投影是两个串行 kernel，中间物化 [padM,Dp] attn GM workspace + 一次 launch。融合为单 kernel：Phase 1 MIX attention 写 attn [padM,Dp] → `SyncAll<true>` GM grid barrier 分隔 → Phase 2 AIC outproj 直接读 attn 并写 out [M,D]，L0A/L0B/L0C 两阶段共享（单次分配 max，顺序执行无 WAR）。消除 1 次 launch + attn GM 往返 + host outF32->out copy。

## 适用场景
- MIX attention（AIC QK^T/PV + AIV softmax）后接 cube outproj 的融合 attention 算子
- fp16/bf16 native 投影 BLOCK_M 小（16）导致 cube 利用率低的算子
- 已建立 cube 路径（P120/P121）的 FA/GQA/MLA 大 case

## 实现要点
1. **SyncAll<true> 分隔两阶段**：Phase 1 MIX（AIC+AIV 协同）完成后 grid barrier，Phase 2 纯 AIC outproj。必须确认 SyncAll 在目标平台可用且不 deadlock。
2. **out 直写 [M,D]**：outproj Fixpipe 用 dstStride=D、nSize 按 D-n0 clamp，D%16==0 时直接写 out [M,D]，消除 host outF32 中间态。非 16 倍数 D 回退 outF32 + host copy。
3. **L0A/L0B/L0C 两阶段共享**：单次分配 max(aL0_attn, aL0_outproj) 等，顺序执行无 WAR，省 UB/L0 预算。
4. **native proj BLOCK_M 16->64 头合并**：手写 mmad 流水在 m=16 时 cube 利用率低，m=64 显著提高（每个 PipeBarrier 摊到 4x 更多 mmad 工作）。task=(b,p,M-chunk)，x M-slice 跨 nH head 复用（x 流量 B*H*3*S*D -> B*3*(H/nH)*S*D），权重跨 nM M-slot 复用。
5. **bf16 P hi/lo 拆分保精度**（配合 X56）：bf16 切 MIX Cube attention 时 P 拆 bf16 hi/lo 两平面累加进 fp32 L0C，恢复 fp32 级精度（bf16 乘积在 fp32 中精确）。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
