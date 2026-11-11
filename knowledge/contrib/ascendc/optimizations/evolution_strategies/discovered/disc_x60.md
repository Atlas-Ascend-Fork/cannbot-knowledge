---
type: Optimization
title: "X60: 向量链发射最小化（代数重写 + calcount 合并）"
description: "当 profiling 显示 Vector busy 高但数据吞吐低、每条向量指令平均耗时接近发射率墙，且 Scalar busy 与 Vector busy 同高时，优化目标应从数据通路带宽切换为指令/发射单元数：用位代数恒等式重写数值链（如伴随掩码 And 替代 floor 取整技巧链），并把多次小 calcount 的同类 API call 合并为一次大 calcount call，减少 scalar call site 的发射与簿记开销。"
tags:
  - task.optimization
  - topic.data_movement
  - topic.programming_model.execution_unit.scalar
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X60: 向量链发射最小化（代数重写 + calcount 合并）

## 核心思路
当 profiling 显示 Vector busy 高但数据吞吐极低（每条向量指令平均耗时接近发射率墙，
Scalar busy 与 Vector busy 同高且来自指令发射）时，优化目标应从"数据通路带宽"切换为
"指令/发射单元数"：(1) 用**位代数恒等式**重写数值链——如用伴随掩码 And（b&0x08）替代
floor 取整技巧链（x*k+c 后 cast），一条恒等式可证明的位运算等价式可大幅压缩长链的
call 与屏障数；(2) 把 N 次小 calcount 的**同类 API call 合并为 1 个大 calcount call**——
底层微指令流完全相同（wrapper 按 repeat 拆分发射），但每 call 省 N-1 个 scalar call site
的发射/簿记开销。

## 适用场景
- 向量链密集、每个 op 后跟 PipeBarrier、Scalar busy 显著的内核（发射开销主导型）
- 无 vector ShiftLeft/ShiftRight 的老架构（310P/m200 等）上用 half 域乘加技巧模拟位操作的链
  （nibble 提取、位域拆装）——代数重写收益最大
- 症状识别：改动前后 MTE2/MTE3 不变而 Scalar busy 大幅下降 = 发射开销被压缩的直接证据
- Gather 类 API：多次 128 元素 call 合并为单个大 calcount call（注意 repeatTime 上限，
  m200 Gather 每 repeat 128 half、wrapper 拆分不改变微指令流）

## 实现要点
1. **恒等式必须代数可证**（不是数值近似）：例 valLo = t - 16*floor(t/8) ≡ t - 2*(b&0x08)；
   valHi = floor(byte/16) ≡ (int8 重解释 b&0xF0)*0.0625（精确 2 的幂除）。逐位一致红线保持
2. **call 合并的硬件约束先查头文件**：Gatherb 在 m200 显式 NOT_SUPPORT；Gather 仅 2/4 字节
   类型、每 repeat 上限 128 half——先排除死路再设计（本策略与 X59 的批放大正交：X59 放大
   数据粒度，X60 压缩指令粒度）
3. **屏障精简逐条分析**：dst 不相交的相邻 op 背靠背发射免屏障；真 WAR/RAW 边保留
   （同 pipe 指令按序发射是前提）
4. **收益判据**：发射单元数下降比例 ≈ Scalar busy 下降比例；Vector busy 下降幅度与被删
   call 数、窗口数成正比

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。

## 补充判据（跨算子复核）

- **循环不变量基向量外提**：`CreateVecIndex + Muls` 生成 `-[0..S-1]` 这类与迭代无关的掩码基向量，若在每轮 TOPK 内重复生成，会多付两条向量 op + 一次 barrier；提到循环外只算一次，内层只保留 `Adds(cond)+clamp+fv`，可稳定拿到 +2% 量级。
- **边界**：只适用于与迭代索引无关的基向量；如果基向量依赖每轮变化的 `tk/bt`，不能外提。
