---
type: Optimization
title: 跨内层 tile 复用不变操作数的片上 L1 持有（按外层 task 寻槽）
description: 将每个内层 tile 从 GM 加载的不变操作数改为跨内层 tile 的 L1 复用
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/06-cross-inner-tile-invariant-operand-l1-reuse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：跨内层 tile 复用不变操作数的片上 L1 持有（按外层 task 寻槽）

> 单一优化点：当一个 cube（矩阵乘）阶段在外层 task 循环内还嵌套一层内层 tile 循环，且某些 GM 操作数在内层 tile 维度上不变（其 GM 寻址偏移不含内层 tile 索引项），而 baseline 在每个内层 tile 都从 GM 重新搬入这些不变操作数（含 ND→NZ 重排搬运，标量参数设置极重）时，改为：每个外层 task 只在其首个内层 tile 搬入一次不变操作数到片上 L1，跨该 task 的全部内层 tile 复用同一 L1 tensor，末个内层 tile 用完才释放。**关键正确性点**：当本阶段处于"producer 阶段先行"的软件流水（下一迭代的 producer 可能早于上一迭代的 consumer 结束）时，不变操作数的持有槽位必须按**外层 task 标识符对槽数取模**寻址，而不能按内层 tile 索引取模——否则相邻 task 的首个内层 tile producer 会与上一 task 的末个内层 tile consumer 竞争同一槽位而别名覆盖。

---

## 1. 原理

一个 cube 阶段常按"外层 task × 内层 tile"二维划分工作量（外层 task 切分大维度如 batch / head / 行块，内层 tile 切分另一维如列块）。若某操作数只依赖外层 task 维度、不依赖内层 tile 维度，则它在同一 task 的所有内层 tile 中是同一份数据。baseline 通常让每个内层 tile 自包含地从 GM 重新搬入全部操作数（因为 ND→NZ 重排搬运的标量参数设置很重，且 depth 为一的队列无跨迭代缓存），导致这份不变数据被重复搬入"内层 tile 数"次。

把不变操作数的 GM→L1 搬入从"每内层 tile"提升到"每 task 首个内层 tile 一次"，并用持久持有的 L1 tensor 跨该 task 的全部内层 tile 复用，可成倍削减 GM→L1 搬运量与重排搬运的标量参数设置次数，直接降低 cube 侧 MTE2 与 Scalar 开销。即使整体关键路径不在 cube 侧（如 vec 侧更长），cube 提早释放也能收紧 cube 与 vec 的交接、缩短 vec 空闲，带来可测的端到端收益。

---

## 2. 性能问题模式

baseline 的单内层 tile 自包含加载（伪代码，仅示意结构，非真实符号）：

```text
for each outer task:
  for each inner tile:
    producer stage of this inner tile:
      reformat-copy invariant operand from GM to on-chip L1    # every inner tile: redundant reload
      reformat-copy tile-varying operand from GM to on-chip L1 # changes per inner tile, correct
      compute, consuming the invariant and tile-varying operands
      free the invariant operand; free the tile-varying operand
```

问题：不变操作数每个内层 tile 都重新做一次重排搬运（ND→NZ，是标量参数设置最重的搬运之一），重复搬运次数等于内层 tile 数。tile-varying 操作数确实随内层 tile 变、必须每 tile 搬；但不变操作数不变、不该每 tile 搬。队列 depth 为一使跨迭代复用完全丧失。

---

## 3. 正确性红线

1. **持有槽位按外层 task 标识符取模寻址，禁止按内层 tile 索引取模。** 在 producer-first 软件流水下，下一 task 的首个内层 tile 的 producer 可能早于上一 task 的末个内层 tile 的 consumer 执行；若两者落到同一 tile 索引槽位，producer 会覆盖 consumer 尚未读完的数据。按 task 标识符对槽数取模（相邻 task 落不同槽）可消除该别名。
2. **持有槽位数不少于软件流水的复用距离。** producer-first 的一迭代代理距离要求至少能覆盖复用距离的槽位数（典型为双槽：当前 task 与下一 task 并存）；depth 不足会死锁或别名。
3. **load 与 free 严格配对，且仅在每个 task 的首、末内层 tile 触发。** 首个内层 tile 执行 AllocTensor 并搬入，末个内层 tile 执行 FreeTensor；中间各内层 tile 既不搬入也不释放，只读已持有的 tensor。漏 free 会泄漏槽位，使后续 task 的 AllocTensor 阻塞；多 free 会释放仍被本 task 后续 tile 读取的数据。
4. **tile-varying 操作数的加载与释放保持 baseline 不变。** 依赖内层 tile 维度的操作数仍每 tile 搬入、每 tile 释放，沿用原 tile 索引寻槽。
5. **不动跨核同步 flag、不动数据 ring 寻址。** 本策略只改不变操作数的 L1 加载/释放时机与槽位寻址；producer 与 consumer 之间的跨核 flag、workspace 数据 ring 的槽周期保持原样（flag 周期与 data 槽周期可能互质，勿混淆或合并）。
6. **不变性必须由 GM 偏移公式证明。** 不变操作数的 GM 寻址偏移在公式上不含内层 tile 索引项（与"按外层 task 缓存的统计量"等价的不变性依据）；若偏移含内层 tile 项则不可复用。

---

## 4. 泛化条件

适用：
- cube 阶段为"外层 task × 内层 tile"二维循环，内层 tile 数大于一。
- 存在内层 tile 维不变的操作数（GM 偏移无内层 tile 索引项），且其 GM→L1 搬运为重标量参数的重排搬运（如 ND→NZ）。
- 片上 L1 容量允许跨 task 持有不变操作数的并存槽位（槽数 × 单 tensor 大小 ≤ L1 预算；复用既有 depth 不小于复用距离的队列通常无需扩容）。
- 阶段处于 producer-first 软件流水，或可安全按 task 寻槽的等价调度。

不适用：
- 内层 tile 数等于一（无重复可消除）。
- 所有操作数都依赖内层 tile 维（无不变操作数）。
- 不变操作数已在更高层（跨 task）缓存——那是另一层策略，勿重复套用。
- 阶段非 producer-first 且无跨迭代并发持有需求时，按 task 寻槽的复杂度可能不必要。

---

## 5. 实施步骤

1. 识别 cube 阶段的"外层 task × 内层 tile"循环结构，列出每个操作数的 GM 偏移公式，标记哪些在内层 tile 维不变（偏移无内层 tile 索引项）。
2. 选定不变操作数的持有队列，确认其 depth 不小于复用距离（不足则提升 depth，并核算 L1 容量是否超限）。
3. 引入"外层 task 标识符"（如 task 线性编号），在把线性 tile 反解为 (task, inner tile) 时一并填入运行信息结构。
4. 在 producer 阶段：tile-varying 操作数按原样每 tile 搬入（按内层 tile 索引寻槽，不变）；不变操作数仅在该 task 首个内层 tile 搬入，写入"task 标识符对槽数取模"的槽位；其余内层 tile 跳过搬入，直接复用该槽 tensor。把计算面向的成员分别指向 task 槽（不变操作数）与 tile 槽（tile-varying 操作数）。
5. 在 consumer 阶段：把不变操作数的计算面向成员指向 task 槽；tile-varying 操作数指向 tile 槽；tile-varying 操作数每 tile 释放（不变）；不变操作数仅在该 task 末个内层 tile 释放（task 槽）。
6. 保持所有跨核 flag、数据 ring 寻址、Fixpipe 写出目标与字节、原子累加区域不变。
7. 编译 → 全量精度 → 多次 perf 取样对比 baseline（同卡、同编译选项）。

---

## 6. LLM 前置问题

- 目标 cube 阶段是否"外层 task × 内层 tile"二维循环？内层 tile 数是多少？
- 哪些操作数的 GM 偏移在内层 tile 维不变？给出偏移公式核对（是否含内层 tile 索引项）。
- 阶段是否 producer-first 软件流水？producer 与 consumer 的并发持有距离是多少（决定最少槽位数）？
- 不变操作数的持有队列当前 depth 是多少？提升到复用距离后 L1 峰值占用是否超限？
- 是否已有按外层 task 缓存该操作数的更高层策略（避免重复套用）？
- 不变操作数的搬入是否为重标量参数的重排搬运（决定收益量级）？

---

## 7. 验收标准

- 编译通过；全量精度用例通过，与 baseline 结果一致。
- 端到端 task duration 多次取样后较 baseline 有超噪声的可测收益（cube 为关键路径时收益直接且显著；vec 为关键路径时收益间接但应可测）。
- cube 侧 MTE2（GM→L1）搬运量与重排搬运的标量参数设置次数，按"不变操作数份数 ×（内层 tile 数 − 一）"的量级下降。
- 槽位无别名（producer-first 下相邻 task 落不同槽），load 与 free 配对无泄漏、无过早释放。

## 检索卡（短卡）

动作：将每个内层 tile 从 GM 加载的不变操作数改为跨内层 tile 的 L1 复用
适用：cube 阶段具有外层 task×内层 tile 二维循环，且内层 tile 多于一个
限制：持有槽位须按外层 task 标识符取模，禁止按内层 tile 索引取模
范围：cube 矩阵乘的外层 task×内层 tile 循环
检索词：外层 task、内层 tile、GM 偏移、L1、不变操作数
机会：操作数的 GM 偏移无内层 tile 索引项
