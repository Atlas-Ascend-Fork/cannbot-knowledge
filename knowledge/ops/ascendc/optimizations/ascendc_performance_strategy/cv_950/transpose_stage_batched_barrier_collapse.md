---
type: Optimization
title: 转置段批量化与屏障对合并（按通道分形批 / 跨 fi 融合）
description: 把转置段逐分形的「读+双全屏障+转置+写」按通道分形批（B=4~16）或跨 fi 融合（F≈32~40）合并，批边界落在同一 batch 元素内。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/37-transpose-stage-batched-barrier-collapse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：转置段批量化与屏障对合并（按通道分形批 / 跨 fi 融合）

> **来源：A5 自由探索实测（linear_permute_sigmoid_mul，2026-09-17，107 裸机）**
> direction_key: `v0-per-fractal-copy-barrier-serialization::batched-multifractal-ub-staging::v0-processstrip-hotloop`（实例一）；`v0-fi-axis-batch-barrier-serialization::cross-fi-fused-slab-staging::v0-processstrip-hotloop`（实例二）
> 证据：<AOA_ROOT>/campaigns/linear-permute-sigmoid-mul-kb-a5-107-20260917-opencode/framework/aoa_out/linear_permute_sigmoid_mul_custom/loop_<run-id>/explore/direction_002/
>       <AOA_ROOT>/campaigns/linear-permute-sigmoid-mul-kb-a5-107-20260917-opencode/framework/aoa_out/linear_permute_sigmoid_mul_custom/loop_<run-id>/explore/direction_003/
> 实测：实例一 1.4426 x（geomean 40.7048→28.2172us，general0/5 1.62x、general22 1.78x、general23 1.43x、general24 1.60x，零回退）25/25；实例二 1.0354 x（geomean 28.2077→27.2438us，general18 1.126x，最差 case -0.63% 落在噪声带）25/25。两者均按位等价（x_perm 逐字节相同）。

## 原理

转置热点（`ProcessStrip` 形态）按 16×16 分形循环执行：每个分形「一笔小额带步距读 → `PipeBarrier<PIPE_ALL>` → 16×16 转置 → `PipeBarrier<PIPE_ALL>` → 一笔小额写」，即每 512B 载荷**两次全流水排空**，整个转置被逐分形串行化（校准成本 0.171~0.180us/分形）。

批量化分两级：

- **按通道分形批（实例一）**：在单个 batch 元素的像素子段内，把通道分形循环按批 B=4~16 组织——(1) 一次 `DataCopyPad` 读 `[Bch × px]` 通道 slab（blockCount=Bch，同 srcStride，目的连续 UB 板），取代 Bch 笔 16 行微拷贝；(2) Bch 个 16×16 转置排在**单对** `PIPE_ALL` 之间；(3) 转置后的 `[px × Bch*16]` 块按行连续段一笔（或每批一笔）写回，取代 px×32B 的微写。UB 用量从 1KB 升到约 4~20KB（lane 预算约 124KB）。
- **跨 fi 融合（实例二）**：把同一 m-条带内的 8 个 fi 批次合并进**一个**屏障覆盖范围：逐 fi 的 slab 读背靠背发起（各自独立 MTE2，落各自的 512B 对齐 slab 区），再单对 `PIPE_ALL`，再对融合范围连续做全部 16×16 转置，再按原写形态写。融合宽度 F≈32~40 分形/屏障对（slab 缓冲扩到 2×20KB，仍落在 ≥44KB 空闲预算内），每 strip 屏障对从 16 降到 7~8。

## 性能问题模式（哪些 profiling 信号说明该用）

- 转置段内每个 32B~512B 载荷都伴随一对全流水屏障（读→转置→写三轮转换的 turn-around），指令数与分形数强相关。
- 转置段在整个 strip 时间线里仍占 30~60%（提升后仍在闸门位），而单位分形成本乘分形数就能解释耗时（说明不是数据量问题）。
- 多 lane 并发时同一批次的耗时显著高于单 lane（实测低争用 ~1.05us/批 vs 8-lane 争用 ~1.7~1.8us/批），指向共享管线/L2 争用。
- 写侧仍是逐分形微事务（每 strip 数百笔小描述符），与读侧已批量化的形态不对称。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **批边界必须落在同一个 batch 元素内**：`HW % 16 != 0` 的算子存在 batch 边界切分，融合/批处理必须在边界处按既有子段循环切开（实例二的 D6 语义），否则跨元素取数出错。
2. **UB 预算与槽地址**：V0 lane 的 slab 缓冲扩容（1KB → 4~20KB；2×8KB → 2×20KB）必须落在该 lane 的空闲预算内（约 124KB − C2V 槽 64KB − 其它 slab）；C2V 槽地址在 lane 分支前由所有角色按同式分配，**不得改动**。
3. **按位等价**：同一批 16×16 转置、同值、同序，只改拷贝粒度与屏障位置——`x_perm` 必须逐字节相同；valid 掩码与尾部处理保持原样。
4. **收益归因要实测，不要照抄假设**：实例二预注册的「每批本征屏障串行主导」假设被单 strip 证伪器证伪（general11 0.994x / general12 1.011x < 1.15x），实际收益来自**共享管线/L2 争用缓解**——因此单 lane / 低并发场景不要预期收益，收益随并发 lane 数出现。
5. **通道分形批的收益前提是逐分形串行形态仍在闸门位**：若读侧已由其它卡（如 14/29）批量化、或转置原语已被替换（18/19/20/21），本条收益显著下降，应先重测单位分形成本。
6. **回退路径保留**：宽写/融合不可表达的形态（不能整除、尾部）保留原逐分形路径。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- shape：C（通道/列）大、条带分形数多、batch 元素数多的 case 收益最大；BIG3 形态（V0 已被完全隐藏）收益小（实例二 1.052~1.082x）。
- dtype：与 dtype 无关（纯搬运/屏障重排），窄 dtype 的每行连续段更小、批量收益更明显。
- 流水线：`aiv_vec` 的转置子段；对任何「逐分形搬运 + 转置 + 逐分形写」的向量核转置热点适用。
- 与 18/19/20/21 的关系：那四张卡**替换转置原语/通路**（显式索引收集、描述符散写、整面板、宽收集），本条**不改原语**，只改分形循环的批与屏障放置——先判断原语是否本身是墙：若是，先上 18~21；若原语尚可而串行化是墙，用本条。
- 与 05 号卡的关系：05 批量化**收尾段**的整块读写与屏障塌缩；本条作用在**转置段**（生产者），两者可叠加且都要复核 UB 预算。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 标定单位分形成本与转置段占 strip 时间线的比例，确认串行化（而非数据量）是约束。
2. 选定批量维度与批宽：通道分形批 B（受 UB 与通道分形数限制）或跨 fi 融合宽度 F（受 slab 缓冲与屏障对数限制）。
3. 重写子段循环：批量读 → 单对屏障 → 批量转置 → 批量写；读侧 blockCount/stride 与写侧 blockLen/stride 按新粒度推导。
4. 在 batch 边界处切分批量（保持原有子段语义）；不可表达形态保留逐分形回退路径。
5. 复核 lane UB 预算与槽地址不变；复核 x_perm 按位等价。
6. 全量精度用例通过后做平衡交替配对测量，并单独报「单 strip / 低并发」与「多 lane 并发」两组数字（收益形态不同）。

## LLM 前置问题（应用前必须自问）

1. 转置段当前的单位分形成本是多少？屏障对总数与分形数的关系是什么？
2. 原语本身是不是墙（是否已由 18~21 处理过）？单位成本是否已经很低？
3. 批量边界会不会跨 batch 元素（`HW % 16 != 0`）？边界切分沿用哪段既有语义？
4. lane 的 UB 空闲预算有多少？扩容后槽地址是否保持不变？
5. 收益是「本征串行消除」还是「共享管线争用缓解」？有单 strip 证伪器数据吗？
6. 回退路径覆盖哪些形态？尾部分形怎么处理？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；UB 用量与槽地址与基线一致（槽地址不动）。
- **精度**：全量用例一次通过（实测 25/25）；**x_perm 逐字节等价**（位等价是硬判据）。
- **性能**：平衡交替配对 geomean 超噪声底（实测 1.4426x / 1.0354x）；报收益随并发度的分布。
- **零劣化判据**：最差 case 回退落在噪声带（实例二 -0.63%）；低并发形态允许持平（不报为收益）。
- **回退**：跨 batch 边界无法切分、UB 预算不足、或按位等价被破坏时，回退逐分形路径。

## 检索卡（短卡）

动作：把转置段逐分形的「读+双全屏障+转置+写」按通道分形批（B=4~16）或跨 fi 融合（F≈32~40）合并，批边界落在同一 batch 元素内。
适用：向量核转置段逐分形双 PIPE_ALL 排空、多 lane 并发下成为稳态门的算子。
限制：批边界须落在同一 batch 元素（HW%16!=0 按边界切分）；lane UB 预算与 C2V 槽地址不得改；x_perm 须逐字节等价。
范围：向量核转置段（生产者 x_perm 热点）的分形循环与屏障放置。
检索词：转置段、屏障塌缩、PIPE_ALL、分形批、跨 fi 融合、slab staging、x_perm、lane 争用。
机会：每 512B 载荷两次全流水排空；转置段占 timeline 30~60% 且多条 lane 共享 MTE3/L2。
代价：UB 增长（双 slab ~4-40KB）；收益来自共享管线/L2 争用缓解，单 strip 可能不赚。
