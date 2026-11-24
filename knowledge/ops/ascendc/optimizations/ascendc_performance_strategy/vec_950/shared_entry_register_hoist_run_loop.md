---
type: Optimization
title: 共享小表条目的寄存器外提（run 外层 + 行内层）
description: 把行循环改成“共享 run 外层 + 行内层”，每 run 只装载并宽化一次表项、驻留寄存器供 run 内各行复用
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/shared-entry-register-hoist-run-loop.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：共享小表条目的寄存器外提（run 外层 + 行内层）

在行式算子里，如果连续 R 行共享同一条小表项（位置编码的 cos/sin、mask、per-channel 参数），把“每行重装这条表项”提到 run 外层、让表项驻留寄存器，收益远大于“少几条向量指令”的算术预期。

## 1. 原理

行式算子的 per-row 成本有三块：

1. 数据行本体：`x0/x1` 装载 + 6 条算术 + 窄化 + store；
2. 表项定位与装载：`cs + e(r)*pitch` 的地址算术 + `DIST_UNPACK_B16` + `Cast`（b16 时）；
3. 循环控制与掩码/地址寄存器重建。

当 R 行共享一个表项时，②③ 是纯重复。在 b16 / H=64（D=128）的 half 行式路径上：

外提后内层循环里几乎没有标量。UB 读字节数几乎不变而墙钟明显下降，说明原本卡在发射/依赖上，而不是卡在 UB 带宽上。

## 2. 性能问题模式

- 优化目标：消除“共享表项”的重复装载与随之而来的标量地址算术。
- 适用数据流：行式 elementwise / 位置编码 / norm；表项按 s、按 head-group、按 block 共享。

## 3. 正确性红线

- run 起点可不对齐：tile 起点落在 run 中间时，首 run 长度 = `R - start % R`，末 run 被 tile 高度截断。
- b16 宽化掩码用行宽 `H`，不是 `VL`；`H = VL/2` 时上半区不是有效数据。
- `R == 1` 的路径必须切到 row-order 变体（否则 run 循环本身成为新瓶颈）。
- 表项 pitch 必须 32B 对齐（dtype 变了 pitch 跟着变）。

## 4. 泛化条件

- 策略作用域：common。
- 适用：同一表项被连续 R>=2 行共享；表项宽度 H <= VL；行在 UB 里步长固定。
- 不适用：每行表项都不同（s-fastest 展平的 layout1）；表项宽度 > VL；表项依赖行内数据。
- 与 `per-row-mask-addrreg-hoist` 的分工：本卡只在 R>=2 时成立；R==1 时 run 循环退化为纯开销，必须切那张卡的 row-order 逐行变体。
- 与 `covh-init-precompute-ub-resident` 的区别：那张卡把不变量提升成 Init 期一次生成、整 kernel 生存期的 **UB 常驻表**（有容量守卫）；本卡的表项是**寄存器常驻**、生存期只覆盖一个 run（无需容量守卫），因此不必为 UB 预算重新推导 tiling。

## 5. 实施步骤

1. 写出显式映射 `e(r)`，确认它是分段常量。
2. 由 tile 起点算出首 run，再与 tile 高度取 min。
3. `while (r < rows)`：装载+宽化表项到寄存器；内层 `for (rr=r; rr<r+run; ++rr)` 只做行本体。
4. run 结束：`r += run; e += 1; run = R`（末 run 用 min 收敛）。
5. `R` 恒为 1 时改走 row-order 变体。
6. A/B 时核对 UB 读字节数几乎不变、墙钟显著下降（证明瓶颈是重复指令而不是字节）。

## 6. LLM 前置问题

- 行→表项的映射是什么？同一表项被连续多少行共享？
- tile 起点是否对齐 run 边界？首/末 run 长度怎么算？
- 表项是 b16 还是 f32？宽化做几次？
- `R` 会不会退化到 1（例如 N==1 的 layout）？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`common`
- 相关策略：`per-row-mask-addrreg-hoist`（R==1 的变体）、`covh-init-precompute-ub-resident`（UB 常驻表对照）

## 检索卡（短卡）

动作：把行循环改成“共享 run 外层 + 行内层”，每 run 只装载并宽化一次表项、驻留寄存器供 run 内各行复用
适用：同一表项被连续 R≥2 行共享；表项宽度 H≤VL；行在 UB 里 pitch 固定
限制：首 run=R−start%R、末 run 被 tile 截断；b16 表项每 run 只宽化一次；R==1 必须切 row-order 变体
范围：行式 elementwise / 位置编码 / norm 的逐行查表路径
检索词：run 循环、表项外提、寄存器驻留、单次宽化、DIST_UNPACK_B16、partial run
机会：每行重装同一条小表项，表项定位与宽化是纯重复，还带出一串标量地址算术
代价：多两个常驻向量寄存器；run 边界算错会整行错位
