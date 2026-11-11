---
type: Optimization
title: "X184: 相邻 AIV 子核合并：先查并行度，再算 launch 节省"
description: "把相邻 AIV 子核（如 pad + im2col + snap）合并成一个 kernel 时，收益主要来自并行网格的变化（例如 B×groups → B×C，填满空闲 AIV 核），而不是省一次 launch。合并前先算父 kernel 的“启动 block 数 vs 实际干活的 block 数”；若父 kernel 本来就更满了，合并的收益会很小。"
tags:
  - task.optimization
  - topic.parallelism
  - topic.compute.composite
status: draft
sources: []
created_at: "2026-11-05T00:00:00Z"
updated_at: "2026-11-05T00:00:00Z"
platforms:
  - a2
  - a3
---
# X184: 相邻 AIV 子核合并：先查并行度，再算 launch 节省

## 现象

多个相邻的 AIV 子核（如 pad、im2col、snap）常被合并成一个 kernel，理由通常是“省一次 launch + 省一次中间往返”。但在实际 profile 里：

- launch 开销只占几个微秒；
- 真正的收益来自**并行网格的变化**：父 kernel 可能按 `B×groups×Ci` 启动 block，但 body 只迭代 `B×groups`，大量 block 空跑；合并后按 `B×C` 重新划分，才把所有 AIV 核填满。

如果把收益全部归因于“省 launch”，下次遇到父 kernel 已经满载的场景就会误判。

## 根因

- 父 kernel 的 grid 维度与 body 实际迭代维度不一致，存在“空跑 block”；
- 合并后重新设计 grid，才把隐藏的并行度释放出来；
- 省 launch / 省中间 GM 往返是次要项，量级通常只有 1% 以内。

## 判据

1. **先算有效并行度**：父 kernel 启动了多少 block、其中多少个 block 真正做了 work；若空跑比例高，合并有并行度红利。
2. **分别估算两项收益**：
   - launch 节省 ≈ 每次 launch 的固定开销 × 合并掉的 launch 数；
   - 并行度收益 ≈ 空跑 block 占比 × 父 kernel 时间。
   若后者远大于前者，合并的主要理由是并行度。
3. **合并后必须重算 grid**：不要沿用父 kernel 的 grid；按合并后的工作项重新划分 block，确保每个 block 都有活。
4. 若两个父 kernel 本来都已满载、launch 开销也可忽略，合并的净收益会很小，甚至因 UB 压力/串行化而回退。

## 实现要点

1. 合并前记录每个父 kernel 的 blockDim、实际工作项数、每 block 平均工作量；用这个数据判断空跑比例。
2. 合并时保持 XPc / im2col 生命周期与跨核同步正确；合并后的 kernel 内部按新 grid 重新分配工作。
3. 不要为了“少一次 launch”把两个已经满载的 kernel 强行串行合并；先看合并后单 block 的工作量是否下降。
4. 合并后重新做 UB/workspace 预算审计；两个 kernel 的 buffer 生命周期叠加可能超预算。

## 边界

- 父 kernel 已经满载、launch 开销可忽略：合并收益很小。
- 合并后每 block 的工作量被摊薄、或引入额外串行段：可能回退。
- 两个子核的数据依赖很强、无法真正并行：收益只来自省 launch，量级有限。

## 实测证据

- 在一个 CV attention 算子中，把 pad + im2col + snap 合并成单 AIV kernel 得 **+3.2%**；父 im2col 的 grid 是 `B×groups×Ci`，但 body 只迭代 `B×groups`，大量 block 空跑。合并后 grid 改为 `B×C`，填满全部 AIV 核。省 launch 只占很小一部分。
- 合并后 nSplit 减半换大 sN 是净中性（约 0.0%），说明收益不是来自 GEMM tiling，而是来自 AIV 侧并行度。

## 关联

- 融合拓扑：[P121](../cards/p121_fa_splitfuse_cv_pipeline.md)、[X14](disc_x14.md)。
- 多阶段拆分：[P88](../cards/p88_multiphase_compute_phase_decomposit.md)。
- 任务调度与 grid：[P126](../cards/p126_gm_tiling_table_task_schedule.md)、[X140](disc_x140.md)。
