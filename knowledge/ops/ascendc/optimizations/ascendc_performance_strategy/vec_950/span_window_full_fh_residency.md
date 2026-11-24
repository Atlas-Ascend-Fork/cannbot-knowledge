---
type: Optimization
title: 整段 span × 全 fh 行的 UB 窗口常驻
description: 把 span 缓冲从“1 行双槽”扩成“fh 行双槽”，一列的所有 tap 地址落在同一块 UB，行越界用整行 -inf 填充
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/span-window-full-fh-residency.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：整段 span × 全 fh 行的 UB 窗口常驻

把一个 tile 的 span 缓冲从「1 行双槽」扩成「fh 行双槽」，使任意 (列,tap) 地址都落在同一块 UB 内，从而让计算体按列一次折完所有 tap；行越界用整行 -inf 填充替代 dy 区间裁剪，UB 模型改成 `2*fh*spanCols*cp` 并重解 TX。

## 1. 原理

「能折叠进寄存器」的前提是数据同时可见。原实现把 span 做成**单行双槽**：每个 dy 只把一个源行搬进 UB，算完就换下一行。这样 UB 很省、流水很好，但计算体只能以 `(dy,dx)` 为外层循环、逐列做向量运算——tap 永远在外层，累加器只能落 UB，于是每个 tap 都是 6 次 UB 往返。

把窗口扩成 fh 行后，任意 (列, tap) 的地址 `(dy*sc + i*sw + rw*dx)*cp + kOff` 都落在同一块 UB 内，计算体才可以「对一列一次走完所有 tap」。这不是预算扩张而是**预算置换**：窗口多占的 `2*(fh-1)*spanCols*cp` 字节，正好被同时删掉的 `partial / acc / fTap / fTiled` 四块缓冲抵掉。

## 2. 性能问题模式

- 优化目标：让同一列的全部 tap 数据同时驻留，解锁「按列折叠 tap」
- 适用数据流：滑窗读取「fh 行 × 连续列段」、且计算体希望按列折叠 tap 的窗口类算子
- 与 `vec-acc-register-resident-tap-fold` 的关系：**该卡是前置条件**，单独使用本卡不会变快（单行→fh 行的直接收益只是省掉逐 dy 重载）；本卡的价值完全体现在「让另一张卡得以成立」

## 3. 正确性红线

- 窗口宽度下界是 `spanCols == sw*(TX-1) + rw*(fw-1) + 1`，任一方向裁短都会让某些 (列,tap) 地址落到窗口外
- 行越界必须重新定义语义：用**整行 -inf 填充**代替 `dyLo/dyHi` 区间裁剪，换来固定长度的 tap 循环
- -inf 填充的地址区间必须与 MTE2 搬入区间**不相交**（前缀/后缀 vs `[lo,hi)`），否则 V 侧填充与在飞拷贝会竞争同一段 UB
- UB 预算模型必须同步改成 `2*fh*spanCols*cp` 并按此重解 TX；沿用旧的 `4*spanCols*cp` 会直接 UB 溢出
- 窗口末列要留 VL 个元素的尾部填充，否则最后一次 `LoadAlign` 读越界

## 4. 泛化条件

适用：

- 计算体要按列折叠全部 tap，因此必须同时看到 fh 行的同一段列
- MTE2 有余量承担「一次搬 fh 行」的突发
- UB 有可双槽流水的余量

不适用：

- UB 放不下 `2 × fh × spanCols × cp` 且 TX=1 仍放不下
- 需要跨 dy 复用同一行缓冲以省 MTE2 字节的场合——本机制不提供（那要行环 + 队列深度对齐，见 `double-buffer-slot-reuse-race`）
- 边界行占比极高、且依赖 dy 区间裁剪省 V 工作的极端形状（整行 -inf 填充会把边界行也按满 tap 计算）

## 5. 实施步骤

1. span 缓冲从「1 行 × 双槽」改成「fh 行 × 双槽」，`InitBuffer` 尺寸 = `(fh*spanCols*cp + VL)` 个元素
2. 搬入改成每个 dy 一次 `DataCopyPad`，落到窗口的 dy 行；行越界的 dy 不搬，整行留给 -inf 填充
3. 计算前对每行填前缀/后缀 -inf（与搬入区间不相交），越界 dy 整行填 -inf
4. tiling 的 UB 模型改成 `2*fh*spanCols*cp + TX*cp*2 + taps*cp*2`，重解 TX 与 spanChunk；只有「整段 span」放得下才启用（`spanChunk == spanCols`）
5. 放不下的极端形状保留「列分块 + 旧计算体」路径

## 6. LLM 前置问题

- 目标实现是否满足：计算体希望按列折叠全部 tap（否则本卡无收益）？
- 目标实现是否满足：`2*fh*spanCols*cp` 能进 UB（含双槽）？
- 目标实现是否满足：MTE2 有余量承担一次搬 fh 行？
- 是否命中排除条件：UB 放不下且 TX=1 仍放不下？
- 是否命中排除条件：形状依赖 dy 区间裁剪省 V 工作、且边界行占比很高？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`op_class`
- 相关策略：`vec-acc-register-resident-tap-fold`（本卡是它的前置条件）、`mte-row-pad-strided-staging`（行槽 32B 垫整）、`double-buffer-slot-reuse-race`（双槽复用边界）

## 检索卡（短卡）

动作：把 span 缓冲从“1 行双槽”扩成“fh 行双槽”，一列的所有 tap 地址落在同一块 UB，行越界用整行 -inf 填充
适用：滑窗按 fh 行×连续列段读、计算体要按列折完所有 tap；MTE2 有余量；UB 能放下 2×fh×span×cp
限制：窗口宽须≥sw*(TX-1)+rw*(fw-1)+1；UB 模型须改 2*fh*spanCols*cp 重解 TX；-inf 区不得与在飞拷贝重叠
范围：滑窗/形态学/窗口归约类算子的 UB 窗口布局
检索词：span 窗口、fh 行常驻、双槽流水、整行 -inf 填充、UB 预算模型、TX 重解
机会：逐 dy 只搬一行，计算体只能按 (dy,dx) 逐列算，同一缓冲被重复搬运
代价：UB 占用翻 fh 倍；边界行按满 tap 计算，边界占比高时反而变慢
