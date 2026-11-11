---
type: Optimization
title: "X23: Batched Spatial 全宽向量化 + 编译器驱动标量预取"
description: "滑窗卷积/相关类算子（kw==1、W 维逐点 FMA）若按「逐输出位置」切任务，每个 Axpy 只利用部分向量 lane，且每个 (co,tap) 一次权重 GetValue() 的 S-pipe 标量读串行化，是大 K 用例的性能杀手。"
tags:
  - task.optimization
  - topic.compute.quantization
  - topic.precision
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X23: Batched Spatial 全宽向量化 + 编译器驱动标量预取

## 核心思路
滑窗卷积/相关类算子（kw==1、W 维逐点 FMA）若按「逐输出位置」切任务，每个 Axpy 只利用 1/4~1/8 的向量 lane（W∈{8..32}，fp32 PAR=64），且每个 (co,tap) 一次权重 `GetValue()` S-pipe 标量读（~43cy/op）完全串行化，是大 K 用例的性能杀手。X23 把**多个连续空间位置打包进全宽向量**：task=(n,cg,od)，acc[G, Hout*W] 一次覆盖整条 od 行的全部 oh 输出，将 P=floor(64/W) 个连续 oh 位置打包进 64-lane fp32 向量，每个 (co,tap) 仅 1 次权重标量读驱动 P*W 宽 Axpy，向量指令数与标量读同时降低 P 倍（理论下限 total_FMA/64）。

## 适用场景
- **算子类型**: 滑窗卷积/相关，kw==1（W 维逐点）、W∈[8,32]、G 路 Axpy 形态；也适用任何「小空间维 + 标量权重驱动向量 FMA」的算子
- **瓶颈类型**: `scalar_loading` / `scalar_compute`（S-pipe 标量读串行化）、向量 lane 利用率不足、`(W,G)->(G,W)` 标量转置

## 实现要点
1. **BS 路径**: task=(n,cg,od)，acc[G, Hout*W]；P=floor(64/W) 个连续 oh 打包进 64-lane fp32 向量；每 (co,tap) 1 次 GetValue 驱动 P*W 宽 Axpy
2. **Boundary 零填充**: x chunk 先 Duplicate 清零，再按每 tap 合法 oh 连续子区间 strided DataCopyPad 加载；compute 保持统一全宽 Axpy（非法位置乘 0 无贡献），零逐元素/逐 tap 有效性判断
3. **Store**: stride==1 时每 co 行 3 次 strided DataCopyPad（主数据 W + 左/右 bias 填充，bvec 行宽按 32B datablock 对齐），避免 (W,G)->(G,W) 标量转置
4. **关键 — 编译器驱动标量预取**: compute 内层 co-loop 加 `#pragma unroll 4`，让编译器对 GetValue(Axpy) 链做软件流水，把 ~43cy S-pipe 标量读延迟隐藏在 4 路 ILP 中。⚠️ 手工把多个 GetValue 读入局部变量再批量 Axpy 会触发编译器**误编译**（结果错误、速度虚高）——必须保持 GetValue 紧跟其 Axpy，只用 pragma 驱动。unroll 过小不足以隐藏延迟，过大则引入调度/寄存器压力；`#pragma unroll 4` 通常处于较优区间，需按 shape 复核

## 约束
- BS 路径要求 W%8==0（x 行 32B 对齐）；W%8!=0 回退逐位置路径
- strided bias 填充每 co 行消耗 Hout*8 float（datablock 对齐填充）的 UB
- 手工多标量预取不可用（编译器 bug），仅能用 `#pragma unroll` 驱动流水

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；全量精度门禁加逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
