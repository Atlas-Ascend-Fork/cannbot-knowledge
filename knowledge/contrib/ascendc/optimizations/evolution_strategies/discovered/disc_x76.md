---
type: Optimization
title: "分组相位化调度（grouped phase-split）：每核 G 块一组、G×MTE2 → G×VEC → G×MTE3，打破同序发射下的 per-tile DMA 往返暴露"
description: "AIV 是同序发射核：`DeQue` 拿到 `WaitFlag(MTE2→V)` 后标量才继续发射下一条指令，逐 tile `CopyIn → Compute → CopyOut` 会让下一个 tile 的 MTE2 等待上一个 tile 的 VEC。分组相位化把每核 tile 流按 G 块一组重排为 G×MTE2 → G×VEC → G×MTE3，以隐藏 per-tile DMA 往返；该形态收益需同窗对照严格裁决。"
tags:
  - task.optimization
  - topic.implementation.synchronization
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# X76: 分组相位化调度（grouped phase-split）

## 核心思路
AIV 是**同序发射**核：程序里先 `DeQue` 拿到 `WaitFlag(MTE2→V)`，标量才会继续发射下一条指令。
经典逐 tile 写法 `CopyIn → Compute → CopyOut` 因此让 **tile t+1 的 MTE2 必须等 tile t 的 VEC 完成才发射** —— 声明的 TQue 深度
（例如队列声明为 3 深）根本没有被当作预取用，每个 tile 暴露一次完整的 DMA 往返。

**分组相位化**把每核的 tile 流按 G 块一组切成三个相位：

```
for each group of G tiles:
    相位 1: 发射 G 次 CopyIn (G×MTE2)          # 全部在飞
    相位 2: 发射 G 次 Compute (G×VEC)          # 与相位 1 的尾部重叠
    相位 3: 发射 G 次 CopyOut (G×MTE3)         # 与相位 2 的尾部重叠
```

UB 占用、队列深度声明、搬运量、tile→核映射、计算链**逐位不变** —— 只改主循环结构
（主循环 + 分组处理函数 + 分组常量 static_assert）。

## 适用场景
- **算子类型**：elementwise / streaming 类（每 tile 独立的 CopyIn/Compute/CopyOut），AIV_ONLY 或 AIV 主导
- **前提**：每核 tile 数 ≥ 3（否则没有组可组，预期中性）；UB 能容纳 G 块同驻
- **瓶颈标签**：no_overlap / mte2_stall / mte3_stall
- **收益状态**：未证实；该调度形态不改变数值与容量语义，但收益必须用同窗未改动对照裁决

## 实现要点
- **组深度 G 需要逐档标定**：按档试 G（2/3）并做同窗重复对照，不要引用单次观测的具体数值。
- 用**声明式 TQue 深度**表达预取，不要手写 prologue / 手工多标量预取
  （X23 记录过手写预取触发编译器误编译；X4 记录过 EnQue/DeQue 同步开销在小工作量上反客为主）。
- 组内每块仍各自 EnQue/DeQue，相位化只改**发射顺序**，不改同步语义；跨相位边界只保留必要的 `PipeBarrier<PIPE_V>`
  （每 tile 必需的 V 屏障不能删 —— PIPE_V 乱序语义陷阱）。
- `static_assert` 约束 G 与 UB 预算，避免编译期静默越界。
- 按档选择调度：每核 tile 数很少的轻载档无组可组，应保留原串行循环，不要为了统一而强行分组。

## 边界 / 否定项
- [negation] **无条件 load-ahead / 加深预取**（同族但不同机制）：短循环与 HBM 驻留形态可能回退，
  单纯增加在飞 MTE2 请求数并不改变带宽 ⇒ 有效的是「按组三相位重排发射」，不是「多发请求」
- [negation] 组深度越大越好：G 增大会让大流式 shape 更容易落回慢模态
- 迁移到其他算子时只能把它当「无害但收益未证实的调度形态」，并且**必须**用同窗未改动对照
  + 至少两次重复来裁决

## 验证方法
- **性能**：同一设备同一窗口内做父变体/未改动对照的 A/B（正反序至少两轮），单 shape 结论必须
  重复至少两次；以绝对时延和配对差值判断，不用跨窗口比值。
- **精度**：跑全量精度用例，逐元素对比参考实现，要求逐 bit 一致（相位化不应改变数值语义）。
- **容量**：审计 UB 预算与分组常量 static_assert，确认 G 块同驻不越界。
