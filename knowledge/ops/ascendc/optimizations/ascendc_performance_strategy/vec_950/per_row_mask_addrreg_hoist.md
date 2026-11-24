---
type: Optimization
title: 行循环内掩码与地址寄存器的常量化外提
description: VF 入口算一次 UpdateMask(H)，行地址改指针算术，删掉 per-row CreateAddrReg 与 rem/isLast/cnt 分支
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/per-row-mask-addrreg-hoist.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：行循环内掩码与地址寄存器的常量化外提

在 `__simd_vf__` 行循环里 per-row 重建掩码与 `AddrReg`，是“为通用性付的税”。fastPath 上 H 是常量、一行恒等于一个块，把这部分外提后，即使没有任何表项复用，也能拿到可测收益。

## 1. 原理

典型写法：

```cpp
for (uint16_t r = 0; r < rows; ++r) {
    uint32_t rem = H - gg * VLF;
    uint32_t isLast = (uint32_t)(gg + 1 == groups);
    uint32_t cnt = VLF - (VLF - rem) * isLast;
    AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(cnt);
    aXy = AscendC::Reg::CreateAddrReg<T>(r, pitchX, gg, VLF);
    aYy = AscendC::Reg::CreateAddrReg<T>(r, pitchY, gg, VLF);
    ...
}
```

它支持任意 H、任意尾块，但每行都要额外付一串标量指令。而 fastPath 上 `H <= VL && VL % H == 0`，一行就是一个常量掩码块：

```cpp
uint32_t remM = H;
AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(remM);   // 一次
for (uint32_t r = 0; r < rows; ++r) {
    RowFast<T>(..., x0Addr + r * pitchX, ..., mask);                  // 指针算术
}
```

标量指令退化为 1 条加法 + 1 条比较。

## 2. 性能问题模式

- 优化目标：把与行无关的掩码 / 地址寄存器 / 循环不变标量移出最内层行循环。
- 适用数据流：一行 = 一个块的所有行式 VF。

## 3. 正确性红线

- 掩码宽度 = H，不是 VL；H = VL/2 时只更新低半区。
- dense 行单元下 `x1 = x0 + H`，行 pitch = D；双段布局 pitch = paddedH，两者不可混。
- 尾行（tile 高度不足一个 tile）不影响掩码（掩码只跟 H 有关）。

## 4. 泛化条件

- 策略作用域：common。
- 适用：H 为常量且 `H <= VL`、`VL % H == 0`；行 pitch 固定。
- 不适用：H 随行变化（尾列 tile）；H > VL（多块）；非仿射地址。
- 与 `shared-entry-register-hoist-run-loop` 的分工：那张卡处理“R>=2 行共享同一表项”的 run 循环；本卡处理表项不复用、只能逐行推进的形态。两者是同一行循环的两种外层组织，`R==1` 必须退回本卡的 row-order 形态。

## 5. 实施步骤

1. 确认 fastPath 条件（`H|VL`、`H*ds%32==0`）。
2. VF 入口算一次掩码。
3. `CreateAddrReg` 全部换成指针算术。
4. `rem/isLast/cnt` 分支整体删除。
5. 通用路径保持原样，只在 fastPath 切新 VF。

## 6. LLM 前置问题

- 一行是否恰好一个块（`H <= VL && VL % H == 0`）？
- 掩码宽度是 H 还是 VL？
- 地址是仿射的吗（行 pitch 固定）？
- 是否还有 per-row 的分支标量（`if (nRemain == 0)` 之类）？

## 7. 分类与关联

- Classification：`validated_strategy`
- Generality：`common`
- 相关策略：`shared-entry-register-hoist-run-loop`（R>=2 的 run 循环形态）

## 检索卡（短卡）

动作：VF 入口算一次 UpdateMask(H)，行地址改指针算术，删掉 per-row CreateAddrReg 与 rem/isLast/cnt 分支
适用：H 为常量且 H≤VL、VL%H==0（一行=一个块）；行 pitch 固定
限制：掩码宽度是 H 不是 VL；dense 与双段两种 pitch 都要对上；H 非 VL 约数时不能套常量掩码
范围：所有 __simd_vf__ 行循环（行式 elementwise、位置编码、norm）
检索词：UpdateMask、CreateAddrReg、常量掩码、pointer induction、标量税、per-row 分支
机会：行循环每行重算 rem/isLast/cnt 再 UpdateMask，标量发射与向量指令抢同一发射槽
代价：H 随行变化的尾列 tile 仍需 per-tile 掩码，不可常量化
