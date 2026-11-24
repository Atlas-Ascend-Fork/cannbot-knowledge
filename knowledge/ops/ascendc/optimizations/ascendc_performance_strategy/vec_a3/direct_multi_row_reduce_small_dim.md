---
type: Optimization
title: 小归约维多行规约直接整段规约（跳过 R×vecWidth 暂存）
description: 删除 R×vecWidth 暂存清零及跨行 Add 累加，改为直接整段规约。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/direct-multi-row-reduce-small-dim.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：小归约维多行规约直接整段规约（跳过 R×vecWidth 暂存）

> 单一优化点：当对很多行各自做一次"小归约维（D ≤ 向量宽度，如 fp32 的 64）"的求和规约时，不要先用 R×vecWidth 的暂存区把每行 pad/累加再规约（暂存量随行数线性膨胀，挤占片上缓存、放大每 tile 流量）；直接对 (R, 行步长) 的源做多 repeat 的整段规约：`mask=D`、`repeat=R`（分批 ≤255）、`srcRepStride=行步长/8`，每 repeat 规约一行前 D 个元素，结果 packed 连续。无需任何与行数成正比的暂存区。

本策略适用于任何"多行各自做小维度（≤向量宽度）规约"的 kernel，与具体算子无关；尤其配合"N≫D 跨行批归约"策略使用。

---

## 1. 原理

整段规约（如 `WholeReduceSum`）每 repeat 对连续 `mask` 个元素做二叉树求和、输出一个标量，repeatTime 控制做几行，`srcRepStride` 控制相邻 repeat 源跳过的 DataBlock 数。把 `mask` 设为归约维 D（≤向量宽度）、`srcRepStride` 设为行步长/8（每 repeat 跳一行），即可一条指令（repeat=R 分批）规约 R 行，每行只读前 D 个有效元素，padding 区因 mask 不读而无害。结果按 `dstRepStride=1` packed 连续排列。

对比"两段式"（先把每行 D 元素跨行 Add 累加进每行 vecWidth 宽的暂存区、再对暂存区整段规约）：两段式需要一个 `R×vecWidth` 的暂存区，其字节数随行数线性增长（行数大时占片上缓存很大比例，迫使 host tiling 给更小 tile、更多 tile、更多每 tile 开销），且每 tile 要清零 + 读/写该暂存区。当 D 本就 ≤ vecWidth 时，两段式的暂存完全多余——直接整段规约即可，暂存区缩到仅为其它用途（如广播 op 的内部暂存）所需的最小值，tile 行数因此可显著放大。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. kernel 对多行各自做 D ≤ 向量宽度 的规约（如小 D 归一化的平方和）。
2. 当前用"清零 R×vecWidth 暂存 → 跨行 Add 累加进暂存 → 整段规约暂存"两段式，或等价的按行 pad 到 vecWidth 再规约。
3. 该暂存区是片上缓存的主要占用之一，限制了 tile 行数（行数小、tile 多）。
4. 小 D 大 N 的 case，每 tile 的暂存清零 + 读/写流量可观。

不适用：D > 向量宽度（一条整段规约装不下，仍需两段式或分块）；行数很少（暂存占用非瓶颈）。

## 3. 正确性红线

- **mask ≤ 向量宽度**：连续模式 mask 取值对 fp32 ≤64、半精度 ≤128。mask=D 必须 ≤ 该 dtype 的向量宽度。
- **srcRepStride 单位**：以 DataBlock（32B）为单位；行步长/8 必须为整数（行步长 32B 对齐）。每 repeat 跳一行。
- **dstRepStride=1**：结果 packed 连续（每 repeat 一个标量），后续向量运算元素数按"行数"计。
- **repeat ≤ 255**：repeatTime uint8；行数 >255 按 255 分批，dst/src 按行步长推进偏移。
- **padding 无害前提**：源 padding 区可为任意值，因为 mask=D 只读每行前 D 个；但要求 cast/平方等前序 op 已把每行前 D 个写成有效值（padding 区无效值不影响）。
- **结果精度**：整段规约的内部二叉树求和顺序与两段式不同，浮点末位可能略有差异；半精度注意：整段规约对半精度中间和有 65504 饱和（大正值可能饱和），若担心可先升 fp32 再规约。

## 4. 泛化条件

适用（任一）：
- 多行各自做 D ≤ 向量宽度 的规约，当前两段式暂存挤占片上缓存或限制 tile 行数。
- 小 D 大 N case 的暂存清零/读写流量占比可观。

不适用（任一）：
- D > 向量宽度（需两段式或分块归约）。
- 行数很少，暂存非瓶颈，直接规约收益小（但仍正确）。

## 5. 实施步骤

1. 确认归约维 D ≤ 向量宽度，且行步长 32B 对齐。
2. 删除"清零 R×vecWidth 暂存 + 跨行 Add 累加"两段式，改为直接整段规约：`reduce(dst, src, mask=D, repeat=R 分批, dstRepStride=1, srcBlkStride=1, srcRepStride=行步长/8)`。
3. 缩减仅供规约用的暂存区到其它用途所需最小值（如广播 op 内部暂存 ≈ R·vecWidth 元素量级），同步更新 host tiling 的 rowBytes 计入与 tile 行数公式。
4. 全量编译，精度全过（相对误差，注意半精度饱和），多次取样性能。
5. 重点看小 D 大 N case：tile 行数是否放大、每 tile 暂存流量是否消失；改善超噪声且精度过则采纳，否则回退。

## 6. LLM 前置问题

- 归约维 D 是否 ≤ 向量宽度？当前是否用 R×vecWidth 暂存的两段式？
- 该暂存区是否是片上缓存主要占用、是否限制了 tile 行数？
- 行步长是否 32B 对齐（srcRepStride=行步长/8 为整数）？行数 >255 是否按 255 分批？
- 半精度规约是否存在中间和超 65504 饱和风险？是否需先升 fp32？

## 7. 验收标准

- 编译通过。
- 精度：全部用例相对误差不退化（半精度注意饱和与舍入）。
- 性能：小 D 大 N case 的 tile 行数放大、墙钟多次取样稳定改善、超噪声；暂存流量消失。
- host tiling 的 rowBytes 与 kernel 暂存分配一致（避免片上缓存溢出）。
- D > 向量宽度的 case 不被误纳入（应由规模自适应分派切到两段式/分块）。
- 若任一不满足则回退。

## 检索卡（短卡）

动作：删除 R×vecWidth 暂存清零及跨行 Add 累加，改为直接整段规约。
适用：多行小维归约中 D≤向量宽度，且两段式暂存限制 tile 行数或清零、读写占比可观。
限制：归约维 D 须不超过向量宽度，行步长须32B对齐。
范围：多行各自执行的小维求和归约。
检索词：WholeReduceSum、repeatTime、srcRepStride、R×vecWidth
机会：R×vecWidth暂存挤占片上缓存、限制tile行数，或清零/读写流量占比可观。
