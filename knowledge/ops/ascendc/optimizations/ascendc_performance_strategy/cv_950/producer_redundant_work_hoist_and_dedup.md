---
type: Optimization
title: 生产者侧冗余工作提升与去重（消除按 (m,n) tile 放大的重复生产）
description: 宿主把 round-robin 任务序换成每核连续 m-块核亲和映射，生产者条带级工作提出 n 循环、握手重定标到条带级；环槽写降为每 M-行块一次、消费者按绝对地址解析。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/36-producer-redundant-work-hoist-and-dedup.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：生产者侧冗余工作提升与去重（消除按 (m,n) tile 放大的重复生产）

> **来源：A5 自由探索实测（linear_permute_sigmoid_mul，2026-09-17；linear，2026-09-16，107 裸机）**
> direction_key: `v0-transpose-n-tile-redundancy::m-major-chunk-strip-hoist::v0-producer-task-mapping`（实例一）；`mte2-a-operand-traffic::a-ring-rowblock-dedup::v0-c0-ring-layout`（实例二）
> 证据：<AOA_ROOT>/campaigns/linear-permute-sigmoid-mul-kb-a5-107-20260917-opencode/framework/aoa_out/linear_permute_sigmoid_mul_custom/loop_<run-id>/explore/direction_001/
>       <AOA_ROOT>/campaigns/task-0195-linear-a5-107-20260916-opencode/framework/aoa_out/linear/loop_<run-id>/explore/direction_002/
> 实测：实例一 1.3328 x（geomean 54.292→40.736us，matmul 重 case 4.1~5.5x，C=512 档 2.7x）25/25；实例二 1.1030 x（geomean 15.8702→14.3886us，4 个 gridN≥8 大 case 1.54~1.83x，gridN=1 小 case 落在噪声带 0.982~1.006）22/22 且逐 case 指标与基线完全一致。

## 原理

当生产者段（转置/cast/布局重排）被嵌在 `(m,n)` tile 循环**内部**时，凡是与 n 无关的生产工作都会被**重复 numNBlocks 遍**：实测一条 m-条带被冗余转置 numNBlocks 次（C=2048 → 16x、C=1536 → 12x、C=1024 → 8x），环槽里同一行块的 cast 窗口被重复写 gridN 遍。生产者的 MTE 量与转置指令数因此是必要量的 numNBlocks 倍，成为 V-C-V 稳态流水的前端闸门。

两条互补改法：

- **条带级提升（实例一）**：(1) 宿主把扁平 round-robin 任务序（`taskId = mIdx*numNBlocks + nIdx`，stride-32 跨核）换成**每核连续 m-块核亲和映射**（每核独占整 m-块及其全部 n-tile，每核 tile 数仍平衡在 1 以内）；(2) 内核把 `ProcessStrip` 从 n-tile 循环里提出 → 每核每条带只做一次转置（工作 ÷numNBlocks）；(3) 握手标志同步重定标：条带级的 XPRIME 按条带设/等，LINRAW/SLOT_FREE 保持 per-tile，set/wait 计数每 launch 净零。
- **行块级去重（实例二）**：环槽写入从 per-tile 去重到 per-M-行块——每个行块的 cast 窗口只写一次（原为 gridN 份相同拷贝），C0 侧按绝对地址（`wsF_` 形态）从属主核的环槽槽位解析自己 tile 的 A 窗口；跨核 GM 读的安全性由「V0 与 C0 是分开的流序 launch」保证。

## 性能问题模式（哪些 profiling 信号说明该用）

- 生产者段的 MTE 量/指令数与 `numNBlocks`（或 `gridN`）成正比，而数学上只需 1 份——按「条带数 × 列块数」手算即可确认冗余倍数。
- 生产者段校准出的单位成本（实测 0.171~0.180us/分形）与实际耗时按分形数成线性，且提升后该段仍占时间线 30~60%，说明它还在闸门位置。
- 多核轮转指派（stride = 核数）使相邻 tile 落到不同核，共享的面板/条带无法同核复用。
- 数据流图上存在「同一只读输入被多个消费者 tile 各自重读/重写」的形态。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **逐 (m,n) tile 的数值路径必须不变**：Mmad 序列、收尾运算、累加序都不动；提升的只是「与 n 无关的生产工作」。
2. **握手标志重定标后必须配平**：作用域放大（per-tile → per-strip）后要重新核对 set/wait 计数每 launch 净零，并保留 per-tile 的 LINRAW/SLOT_FREE 语义（实测按 AC-054 口径核对）。
3. **跨核读的可见性依赖 launch 边界**：只有「生产者与消费者是两个流序 launch」时，跨核 GM 读才天然安全；若合并成单 launch，必须补显式同步/可见性操作。
4. **核亲和的负载必须平衡**：每核 tile 数差 ≤ 1，且宿主侧计算；否则会引入尾核长尾，吃掉收益。
5. **环槽容量按去重后的行块数重算**：去重改变槽的编号与容量账，与双缓冲/预取深度策略叠加时按最坏组合重算。
6. **无可去重形态时不要强上**：`gridN=1`（或 numNBlocks=1）的 case 没有冗余可去，实测落在噪声带；这部分 case 应保留原路径。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- shape：列块数多（C 大）、条带多的 case 收益最大（实例一 4.1~5.5x）；`gridN=1` 中性。
- dtype：与 dtype 无关（工作冗余与布局重排）。
- 流水线：`aic_mte2` 或生产者向量段；对任何「生产者嵌在 (m,n) 循环内、且部分工作与 n 无关」的矩阵/CV 融合内核适用。
- 与 16 号卡的关系：16 通过核亲和指派让**只读面板**同核驻留复用（减少跨核重读），本条通过核亲和指派 + 循环提升**消除重复生产本身**（写侧冗余），两者可叠加但都必须做负载平衡。
- 与 24/27 号卡（驻留复用）的关系：那两张卡减少的是「重复读」，本条实例二减少的是「重复写」，实例一减少的是「重复算」。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 统计生产者段工作量与 `numNBlocks/gridN` 的关系，确认冗余倍数与消除后的理论上界。
2. 宿主侧把任务序改为每核连续 m-块映射（保持负载平衡 ≤1 tile）。
3. 内核把与 n 无关的生产工作（转置/布局重排）提出来，放到条带级；同步把手握标志重定标到条带级并存证计数配平。
4. 写侧冗余场景（实例二）：把环槽写降为 per-M-行块一次，消费者按属主核槽位绝对地址解析窗口。
5. 复核跨核读的 launch 边界与可见性；复核槽容量。
6. 全量精度用例（含 gridN=1 与尾块）通过后做平衡交替配对测量，并单列「无冗余 case」的噪声带结果。

## LLM 前置问题（应用前必须自问）

1. 生产者段的哪部分工作与 n 无关？冗余倍数是多少（numNBlocks / gridN）？
2. 任务序换核亲和后每核负载还平衡吗？尾核长尾有多少？
3. 提升后要在哪个粒度握手？set/wait 计数每 launch 净零的证据是什么？
4. 跨核读/写的可见性靠什么保证（launch 边界还是显式同步）？
5. 槽容量与编号重算过吗？与双缓冲/预取叠加后是否仍放得下？
6. `gridN=1` 或 `numNBlocks=1` 的 case 走哪条路径？它们的噪声带数据在哪？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；宿主任务映射与内核标志改动同源提交（避免半套改动导致语义错位）。
- **精度**：全量用例一次通过、零修复轮（实测 25/25、22/22）；实例二要求逐 case 指标与基线完全一致（bit 级同字节论证）。
- **性能**：平衡交替配对 geomean 超噪声底（实测 1.3328x / 1.1030x）；收益集中在多列块/多条带 case。
- **零劣化判据**：无冗余 case（gridN=1）落在噪声带（实测 0.982~1.006）且无非预期回退。
- **回退**：负载失衡、标志计数不配平、可见性无法证明、或槽容量不够时回退原 per-tile 生产路径。

## 检索卡（短卡）

动作：宿主把 round-robin 任务序换成每核连续 m-块核亲和映射，生产者条带级工作提出 n 循环、握手重定标到条带级；环槽写降为每 M-行块一次、消费者按绝对地址解析。
适用：生产者段（转置/cast/重排）嵌在 (m,n) tile 循环内、与 n 无关的工作被重复 numNBlocks 遍的融合算子。
限制：逐 (m,n) 数值路径不变；核亲和后负载平衡须 ≤1 tile；去重后槽容量重算；gridN=1 形态无收益走原路径。
范围：融合算子的生产者段（转置/cast/环槽写）与任务映射。
检索词：冗余提升、核亲和映射、n 循环外提、环槽去重、握手重定标、numNBlocks、绝对地址解析、gridN。
机会：同一行块的窗口被重复写 gridN/numNBlocks 遍（实测 C=2048 时 16x）；V0 生产者速率成为稳态门。
代价：去重后槽容量需重算；跨核读依赖流序 launch 边界保证。
