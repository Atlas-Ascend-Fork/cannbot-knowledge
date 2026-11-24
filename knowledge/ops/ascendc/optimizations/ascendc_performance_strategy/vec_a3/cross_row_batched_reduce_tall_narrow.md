---
type: Optimization
title: N≫D 逐行归约改跨行批归约 + 整 tile 批施加
description: 将 N≫D 下的逐行小维归约改为跨行批归约。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/cross-row-batched-reduce-tall-narrow.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：N≫D 逐行归约改跨行批归约 + 整 tile 批施加

> 单一优化点：当一个"逐行做一次小维度归约、再逐行逐元素施加归约结果"的 kernel 面临 N（行数）远大于 D（归约维度）的形状时，每行的固定开销（指令发射、管线屏障、必要时标量同步）会被行数放大成主导成本。把"逐行归约 + 逐行施加"重写为"整 tile 跨行批归约 + 整 tile 批施加"：用跨行 repeat-stride 的二元加 + 多 repeat 的整段规约，一次处理 tile 内所有行；归约得到的每行标量不再下沉到标量寄存器，而是以 packed 向量形式留片上缓存，用向量运算继续算其派生量（如逆缩放因子）并用广播一次性施加到整 tile。整 tile 的向量调用数从 O(行数) 降到 O(1)。

本策略适用于任何「沿一行的小 reduce 维做归约、再把每行标量施加回该行」的 kernel（归一化、reduce-then-scale 等），与具体算子语义无关。

---

## 1. 原理

逐行归约 kernel 的典型实现是：每行 cast/平方、对该行做 tree-fold 或整段规约得到一个标量、再每行用标量广播乘回。当 D 很小、N 很大时，每行真正参与运算的有效元素极少，但**每行的固定开销不变**：一次归约指令发射、若干 `PipeBarrier<PIPE_V>`、且若归约结果下沉到标量寄存器再施加，每行还要一次向量→标量（V→S）同步。N 行累加，这部分固定开销变成端到端时间的大头，远超真正算力/带宽所需。

跨行批归约利用向量单元的高维切分能力：把 tile 内 R 行的数据按 (R, D_align) 连续排布，用一条带 `repeat-stride`（行步长）的二元加，**一条指令的多个 repeat 各处理一行**，把每行 D 个元素累加到一个每行 vectorWidth 宽的暂存区；再用一条多 repeat 的整段规约（每 repeat 规约一行 vectorWidth 宽、行间按行步长跳）把每行压成一个标量，结果 packed 连续排列。这样 R 行的归约从 R 条规约指令降到常数条。

进一步：归约得到的 R 个标量保持 packed 向量形式（不下沉标量、不 V→S），用向量乘/加/开方/除等算出其派生量（每行一个），仍是 packed 向量；再用广播（或 repeat-stride 的标量广播乘）一次性施加到整 tile 的 (R, D) 数据。整 tile 的 V→S 同步从 R 次降到 0 次（施加全部在向量域完成）。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. kernel 结构是"沿每行的小 reduce 维归约 → 每行得一个标量 → 该标量逐元素施加回该行"。
2. 实测或 shape 分析显示目标 case 是 N（行数）≫ D（归约维），D 很小（个位到几十），N 很大（十万到百万级）。
3. 代码审查/profiling 显示：存在 per-row 循环，循环体内有规约指令 + `PipeBarrier`；若施加阶段读标量，还有 per-row 的 V→S 同步。
4. 该 case 实测耗时远高于"纯带宽时间"的一截，且这截与行数（而非有效元素数）成正比；把每行固定开销 × 行数能解释这截的大头。

不适用：D 很大（接近或超 vectorWidth×255，行步长装不下 repeat-stride 的 uint8 上限）时，跨行 repeat-stride 不可用；此时应走逐行/分块归约路径（见相关策略：大 D 分块、规模自适应分派）。

## 3. 正确性红线

- **行步长对齐**：跨行 repeat-stride 以 DataBlock（32B）为单位，故每行在片上缓存须 32B 对齐排布；行步长 = ceil(D·sizeof(elem)/32)·32 的元素数。host tiling 与 kernel 必须用同一个行步长。
- **repeat 上限**：repeat-stride 二元 op 与整段规约的 repeatTime 是 uint8（≤255）。tile 内行数 R > 255 时，必须按 255 分批切分（每批 repeat≤255，dst/src 按行步长推进偏移）。
- **暂存区归零**：若用"先跨行 Add 累加到每行 vectorWidth 暂存区、再整段规约"两段式，暂存区使用前必须整段清零（Duplicate 0），否则残留会污染各行和。
- **packed 结果布局**：整段规约用 dstRepStride=1（按目标元素粒度）时，结果在 dst 连续 packed 排列（每 repeat 一个标量）；后续向量运算的元素数按"行数"计，不要按"行数×槽宽"计。
- **mask < vectorWidth 仍正确**：归约维 D 小于 vectorWidth 时，整段规约用 mask=D（连续模式）只规约每行前 D 个元素；padding 区若为 garbage 不影响（mask 不读）。施加阶段的广播/乘法仍按 (R, 行步长) 布局，padding 区写入无害（搬出时按真实 D 截断）。
- **施加顺序与精度**：把"先算每行标量再施加"改成"批量算 + 广播施加"时，浮点运算顺序可能变化，导致与逐行实现在末位有差异；需以相对误差门槛验收（非逐比特），半精度施加注意舍入模式。
- **同步语义**：归约后标量留向量域、用广播施加时，确保广播 op 与后续读之间有 `PipeBarrier<PIPE_V>`；切勿在施加里漏掉屏障或额外引入标量读而重新引入 V→S。

## 4. 泛化条件

适用（任一）：
- 归一化类、reduce-then-scale 类 kernel，沿每行小 reduce 维归约后逐行施加，且存在 N≫D 的 case。
- 实测耗时 = 带宽时间 + 一截与"行数 × 每行固定开销"成正比的额外开销。

不适用（任一）：
- D 过大，行步长/8 超 uint8 上限（跨行 repeat-stride 装不下）——改用大 D 分块/逐行路径。
- 行数本身很少（每核个位数行），批归约无摊薄对象。
- 归约维跨多行不独立（如需要跨行全局归约），本策略针对的是"每行独立归约"。

## 5. 实施步骤

1. 定位 per-row 归约循环与 per-row 施加循环，确认每行归约维度 D 与行步长。
2. 把 tile 内数据按 (R, 行步长) 连续排布（cast/平方等前序 op 也改成整 tile 一次向量调用）。
3. 实现跨行批归约：清零 vectorWidth 暂存区 → 跨行 repeat-stride 二元加（每行 D 元素累加进暂存区，repeat=R 分批）→ 多 repeat 整段规约（mask=D 或 vectorWidth，repeat=R 分批，dstRepStride=1 packed）。
4. 归约结果 packed 留向量域，用向量乘/加/开方/除算每行派生标量（元素数=行数），全程不做 V→S。
5. 施加：用广播把 (R,1) 派生标量扩成 (R, 行步长)，整块乘到 tile；或用带"共享操作数 repStride=0"的 repeat-stride 乘（见相关策略）。
6. 全量编译，多 shape 精度验收（相对误差，注意半精度舍入），多次取样性能；重点看 N≫D case 的"行数×固定开销"那截是否消失。
7. 改善超噪声且精度过则采纳；否则回退。

## 6. LLM 前置问题

- kernel 是否"每行独立做一次小维度归约、再把每行标量施加回该行"？是否存在 N≫D 的 case？
- 端到端时间里，"行数 × 每行固定开销（指令发射 + 屏障 + 可能的 V→S）"能否解释超出带宽的那截？
- 行步长是否 32B 对齐、是否 ≤ 255·8 元素（repeat-stride uint8 装得下）？行数 >255 时是否按 255 分批？
- 归约结果是否仍下沉标量再施加（引入 per-row V→S）？能否保持 packed 向量、用广播施加以消除 V→S？
- 半精度施加的舍入模式是否与逐行实现一致？精度门槛是相对误差还是逐比特？

## 7. 验收标准

- 编译通过（无新增编译错误）。
- 精度：全部用例相对误差不退化（半精度注意舍入；与逐行实现允许末位差异）。
- 性能：N≫D case 的墙钟多次取样稳定改善且超出噪声；改善量近似等于"行数 × 每行固定开销"的消除量；中小 D 的正常 case 不退化（批归约对它们至少持平）。
- 大 D case 不被误纳入本路径（应由规模自适应分派切到逐行/分块路径）。
- 若任一不满足则回退，记录为该 kernel/shape 不适用。

## 检索卡（短卡）

动作：将 N≫D 下的逐行小维归约改为跨行批归约。
适用：归一化或 reduce-then-scale 内核，逐行小维归约后逐行施加，且 N≫D。
限制：跨行 repeat-stride 以32B为单位，每行片上布局须32B对齐。
范围：逐行小维归约、标量回施路径。
检索词：跨行批归约、tree-fold、repeat-stride、DataBlock、reduce-then-scale
机会：每行有效元素很少，但归约指令发射等固定开销仍逐行发生。
