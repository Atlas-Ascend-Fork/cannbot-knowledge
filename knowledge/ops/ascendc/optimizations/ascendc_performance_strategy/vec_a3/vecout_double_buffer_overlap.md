---
type: Optimization
title: VECOUT 队列双缓冲（写回与下一 tile 计算重叠）
description: 将VECOUT写出队列由单缓冲改为双缓冲，使slot交替使用并重叠写回与后续tile处理。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-vecout-double-buffer-overlap.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：VECOUT 队列双缓冲（写回与下一 tile 计算重叠）

> 单一优化点：AscendC 双队列流水模板中 `TQue<VECIN, 2>`（搬入双缓冲）配 `TQue<VECOUT, 1>`（写出单缓冲）是常见默认写法——每个 tile 的 CopyOut 期间计算停摆。把 VECOUT 队列升为双缓冲（`InitBuffer(outQueue, 2, tileBytes)`），让写回与下一 tile 的计算重叠。

## 1. 原理

- 单缓冲写出队列：kernel 必须等上一 tile 写回完成、slot 归还后才能 EnQue 新结果——MTE3（写出）与 V（计算）/MTE2（搬入）串行化，每 tile 一次显式停顿。
- 双缓冲写出：slot 交替使用，写回(i) 与 计算(i+1) 并行；对每核 tile 数多的大 shape，吞吐由「三段最长者」决定而非「三段之和」。
- 实测（elementwise in-place 算子，40 AIV）：大 shape kernel 时间 -21%~-36%，geo +12%。

## 2. 性能问题模式

- **代码形态**：`TQue<TPosition::VECOUT, 1>` 或 `InitBuffer(outQueue_, 1, tileBytes)`，而 inQueue 是 2。
- **bench 特征**：大 shape（每核 tile 数多）case 与带宽标杆差距 <10% 但始终差一口气；msprof MTE3 占比可观（>15%）且 VEC 与 MTE 时间不重叠。
- **不适用**：UB 预算已近满（多一个 tile buffer 会越界）；每核只有 1-2 个 tile 的小 shape（无重叠窗口）。

## 3. 正确性红线

- **UB 预算按 InitBuffer 全集计算**：模板类常为多 dtype 统一 InitBuffer（含非活跃 dtype 的中转 buf），预算必须按「全部 buffer × 各自 buffer 数 × 每 tile 字节」上界算。本例上界 = 18T bytes（T=tile 元素数）：fp16/bf16 T=8192 → 144KB ✓；若同时把 tile 增到 16384 → 288KB > 192KB → `VEC instruction error: ub address out of bounds` 直接崩溃。
- 越界症状识别：`vec error info: 0x50000003b, mte error info: 0xa00000056`（ub address out of bounds）——回到预算重算，不是数据竞争。
- 双缓冲后 FreeTensor/EnQue 顺序保持模板原语义（Alloc→EnQue→DeQue→Free 链条不变）。

## 4. 泛化条件

- **适用**：一切「CopyIn→Compute→CopyOut」双队列流水的 elementwise/带宽型算子；大 shape case 是主要受益者。
- **不适用**：单 tile 核（无重叠窗口）；输出需与输入同 slot 原地写回且 slot 生命周期纠缠的手动流水（应改手动软件流水）。

## 5. 实施步骤

1. 数 UB：列出全部 `InitBuffer` 调用 × buffer 数 × tileBytes，求和 ≤ UB（910B3 = 196608B），留余量。
2. `TQue<VECOUT, 1>` → `TQue<VECOUT, 2>`；`InitBuffer(outQueue_, 2, tileBytes)`。
3. 若预算不够，先缩 tile 再保双缓冲（本例 tile 回 8192 后通过）。
4. 全量精度 + 大 shape case 前后对比验收。

## 6. LLM 前置问题（实施前自检）

- InitBuffer 全集的 UB 上界（按最大 dtype 字节）算过了吗？tile×buffer 数改动后还 ≤192KB 吗？
- 大 shape case 的 msprof MTE3/VEC 是否本就不重叠（确认是流水问题而非带宽饱和）？

## 7. 验收标准

- build + 精度全过；实测收益（910B3，40 AIV）：大 shape kernel 时间 -21%~-36%，geo 1.687 → 1.895（+12%），20/20 faster。

## 检索卡（短卡）

动作：将VECOUT写出队列由单缓冲改为双缓冲，使slot交替使用并重叠写回与后续tile处理。
适用：适用CopyIn→Compute→CopyOut双队列流水的elementwise/带宽型算子；单tile核不适用。
限制：按全部InitBuffer核算UB并留余量；196608B仅是910B3的预算值。
范围：CopyIn→Compute→CopyOut流水的VECOUT队列。
检索词：VECOUT、双缓冲、TQue、InitBuffer、slot、MTE3、CopyOut、tileBytes
机会：输入队列为双缓冲，而VECOUT或outQueue仍为单缓冲。
