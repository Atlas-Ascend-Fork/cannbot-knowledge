---
type: Optimization
title: "X25: 向量权重广播（Brcb + MulAddDst）替代 S-pipe 标量读"
description: "滑窗卷积/小 GEMM 的瓶颈常是每 (co,tap) 一次权重 GetValue()（S-pipe UB→标量寄存器读，延迟高且依赖链串行）。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
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

# Strategy X25: 向量权重广播（Brcb + MulAddDst）替代 S-pipe 标量读

## 核心思路
滑窗卷积/小 GEMM 的瓶颈常是每 (co,tap) 一次权重 `GetValue()`（S-pipe UB→标量寄存器读，~43cy，依赖链串行）。X25 用 **V-pipe `vbrcb`（Brcb）向量广播** 替代：权重在 GM 预展开为 `[Co,K,8]` 布局（每权重 8 份连续副本），每 (g,tap) 一次 `Brcb` 把 8 个 b32 广播成 64-lane 权重向量，驱动 `numBatches` 条 `MulAddDst`（acc += x*w）——**全程不经过 S-pipe，标量读彻底消失**，数值语义不变。权重跨 oh-batch 不变，batch 循环内移使一次广播覆盖一个权重全部输出位置的复用。

## 适用场景
- **算子类型**: 滑窗卷积 kw==1 / 小 GEMM / 任意「标量权重驱动向量 FMA」且权重跨 batch 复用的算子
- **瓶颈类型**: `scalar_loading` / `scalar_compute`（GetValue S-pipe 串行化为主瓶颈）
- **适用边界**: 多 oh-batch / 多输出位置复用（numBatches≥2）时收益最大；numBatches=1 的高 K 场景收益被 8 倍权重载入抵消

## 实现要点
1. 权重 GM 布局 `[Co,K,8]`：host 侧把权重展开为每权重 8 份连续副本（fp32 PAR=64 → 64/8 副本）
2. x 按 tap 整行加载（rowLen=numBatches*P*W），边界行先 Duplicate 清零再按合法子区间加载，compute 统一全宽
3. `wvec` 用 2×64-lane ping-pong 打破 Brcb→MulAddDst 写后读依赖链
4. ⚠️ 局部调优需保守：unroll 4 + 4 槽 ping-pong 在部分 shape 上可能调度劣化，需按 shape 调优
5. 与 X23 互补：X23 保留 GetValue 但减少数量（hoist）；X25 用 V-pipe 广播彻底消除标量读

## 约束
- numBatches=1 的高 K 场景无跨 batch 摊销，Brcb 的 2-op 代价 + 8 倍权重 GM 载入抵消收益
- W%8==0 满足 32B 对齐门控

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带；收益随 numBatches 变化，按复用度分档核对回退门槛。

## 补充判据（跨算子复核）

- **`Broadcast<2,1>` 本身就是成本**：其内部展开为 `BrcbToOneBlock + Copy + PipeBarrier`；在某 CV 融合卷积的窗口里，1156 cycle/窗口中只有约 33 cycle 是算术，208 repeat 花在广播复制操作数上（约 6.5 倍于计算）。先看广播写与屏障占比，再决定用 Brcb+MulAddDst 还是把广播吸进乘法。
- **路径 A：乘法内建行广播**。当 tile 行宽恰为 1 个 repeat（64 FP32=256B 或 128 FP16）时，`Mul(dst, src0, src1, ..., {1,1,1,8,8,0})` 用 `src1RepStride=0` 让被广播的操作数跨 repeat 复用，一条指令替代 `Broadcast + Mul`。
- **路径 B：Brcb 一次性预展开 + level-0 消费**。行宽不是 1 repeat、或 Dc≥128 硬件无法表达行内恒定步长时，先 `Brcb` 展开一次，再用 `src1RepStride=8` 逐列块复用。
- **路径 C：循环不变量权重预展开**。权重在循环外每 ci 一次 Brcb 展开，窗口内用 `MulAddDst(src0RepStride=0)`。
- **实测**：某 CV 融合卷积的 K1 广播链改 Brcb 预展开 + 2 条 MulAddDst，**+48.7%**（代表 case -57.6%，6 case 位级一致）；某 softmax 逐行链改整块广播 + 归约 + Brcb，+1.6% 独立；某小 matmul 内层删 GetValue 改 Brcb 广播，1.085–1.16x。
- **边界**：路径 A 要求行宽恰 1 repeat；Dc≥128 时行内恒定步长不可表达，改走 B；广播源是循环不变量时优先 C。
