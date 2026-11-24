---
type: Optimization
title: 行内多 tile 延迟归并 + winner tile 重扫（宽行 argmax/argmin）
description: 将行内多 tile 归约改为延迟归并，并在 winner tile 上完成后续处理
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-tile-reduce-slotarray-deferred-winner-merge.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：行内多 tile 延迟归并 + winner tile 重扫（宽行 argmax/argmin）

单一优化点：行长超过单 tile 容量（行必须切成 nTiles 个 tile 串行扫描）的
per-row argmax 类 kernel，把 tile 循环改成「只 ReduceMax 各 tile 最值进
片上槽位数组（零标量打断）→ 行尾一次 ReduceMax(calIndex) 归并出
(行最值, winner tile) → 仅重搬 winner tile 定位首达位置」，把每行标量
回读从 2×nTiles 次降到 3 次、定位链从期望 ~ln(nTiles)+1 次降到 1 次。

## 1. 原理

旧模式在 tile 循环内维护标量 runningMax：每个 tile「ReduceMax → GetValue
（标量停顿，等 VEC 队列排空）→ 若提升则执行 Compares/Select 定位链 →
GetValue」。两个后果：①标量回读打断 MTE/VEC 双缓冲流水（tile 间无法
重叠）；②定位链触发次数数据依赖（随机数据期望 ~ln(nTiles)+1 次/行）。

延迟归并把「比较与定位」全部推迟到数据齐后一次完成：
- tile 循环只发 ReduceMax（calIndex=false），最值写 `maxArr[t*8]`（槽
  间距 8 元素保持 32B 对齐，gap 区一次性预填 -inf，永不被覆盖）；
  循环体内零标量操作，搬运与归约真正流水。
- 行尾对 maxArr 发一次 `ReduceMax(winSlot, maxArr, work, count=
  roundup(8*nTiles,64), calIndex=true)`：gap 区是 -inf 不干扰；calIndex
  返回的元素索引 / 8 = winner tile 序号（首达语义=最左含行最值的 tile）。
- 只重搬 winner tile 一个 tile，执行一次定位（比较链或 calIndex）得
  tile 内首达位置，加 tileStart 偏移即答案。

代价是 winner tile 二次搬运一次（+tileBytes），远小于省下的 nTiles 次
标量停顿与多次定位链。

## 2. 性能问题模式

- per-row 归约行长 > 单 tile 容量（行内 tile 串行循环），且循环内有
  running 标量维护。
- profiling：scalar_ratio 30%+、MTE2 占比低但墙钟高（流水气泡）、VEC
  占比高（定位链低效工作）。
- 典型症状：宽行 case（如 [64,20000]、[1,100000]）明显慢于标杆的
  0.6-0.8x。

不适用：行可整段装入 UB（单 tile 直接 calIndex 一发完成，无需本策略）；
跨行/全局归约（用跨核两阶段类策略）。

## 3. 正确性红线

- **maxArr 槽间距区必须恒为 -inf**：间距 8 中的 gap 7 个元素预填 -inf
  后不得被任何写入覆盖（tile 最值只写槽首），否则行尾归并会把垃圾当
  最值。
- **行尾归并的 count 要 roundup 到 64**（256B 对齐），超出 nTiles×8 的
  部分也必须是 -inf 预填区。
- **winner tile 号 = calIndex 元素索引 / 8**（不是索引本身）。
- **首达语义双重保证**：行尾 calIndex 归并平局取最左 tile；winner tile
  内定位也要首达（calIndex 或严格 > 的定位链）。
- winner tile 的 tileCount 按真实剩余长度（n - tileStart 可能 < TILE_N）。

## 4. 泛化条件

适用：
- argmax/argmin/max-with-idx/min-with-idx 且行长超过单 tile UB 容量；
- 任何「分 tile 串行归约 + 循环内标量 running 状态」的形态（与算子无关，
  定位段可替换为该算子的等价操作）。

不适用：
- 单 tile 能装下的行（直接单次 calIndex）；
- running 状态必须在流式中早期可知（如提前剪枝）的场景。

## 5. 实施步骤

1. 核算 maxArr：maxTiles=ceil(N/TILE_N)，元素数 roundup(8*maxTiles,64)，
   InitBuffer 后一次性按 64 chunk Duplicate(-inf)。
2. tile 循环：TQue Alloc → DataCopyPad(本 tile) → EnQue/DeQue →
   ReduceMax(maxArr[t*8], tile, work, count, false) → Free。
3. 行尾：ReduceMax(winSlot, maxArr, work, roundup(8*nTiles,64), true) →
   GetValue 得 rowMax 与 winTile=elemIdx/8。
4. 重扫：DataCopyPad winner tile → 定位首达（calIndex 两段合成或比较
   链）→ tileStart + localIdx。
5. 输出批量 Cast/DataCopy（沿用行批输出路径）。
6. 精度覆盖：行最值位于不同 tile（首/中/尾）、并列最值跨 tile（首达取
   更左 tile 的更左位置）、尾 tile 非整段。

## 6. LLM 前置问题

- 行长/tile 容量比（nTiles）多大？（nTiles=1 不需要；2-4 收益显著）
- 归约最值的 dtype 与 maxArr 一致性（gap 预填 -inf 对 int 类要换最小值）？
- winner tile 定位段用 calIndex 还是既有比较链（复用旧代码更稳）？

## 7. 验收标准

- 编译通过；精度全过（跨 tile 并列最值用例锁定首达）。
- 每行标量回读 ≤3 次；tile 循环内零标量操作。
- 实测参考（910B3, fp32, TILE_N=6144）：[64,20000] 36.0→23.5us
  （0.80→1.25x）、[1,100000] 32.2→24.1us（0.93→1.25x）。

## 检索卡（短卡）

动作：将行内多 tile 归约改为延迟归并，并在 winner tile 上完成后续处理
适用：适合行长超过单 tile UB、循环内维护标量 running 状态的分 tile 归约
限制：maxArr 槽间 gap 必须预填并始终保持 -inf，禁止任何写入覆盖
范围：argmax、argmin、max/min-with-idx 行归约
检索词：per-row、runningMax、ReduceMax、GetValue、Compares/Select、maxArr、winner tile
机会：per-row 行长超出单 tile，串行 tile 循环内反复维护 running 标量
代价：需配置 maxArr，其容量随 maxTiles 增长并按 64 取整
