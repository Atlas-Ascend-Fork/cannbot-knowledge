---
type: Optimization
title: split-K 消费侧归并的全局行条带摊平（把归并工作从 tile 属主解绑）
description: 把 split-K 消费侧归并从 tile 属主解绑：每 tile 的 baseM 行切自适应条带、(tile,条带) 展平后跨全部 2×usedCores lane 派发，段升序累加。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/38-split-k-consumer-global-striped-merge.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：split-K 消费侧归并的全局行条带摊平（把归并工作从 tile 属主解绑）

> **来源：A5 自由探索实测（stack_addmm，2026-09-14，107 裸机）**
> direction_key: `v1-merge-lane-serialization::global-row-striped-merge::split-k-consumer-merge`
> 证据：<AOA_ROOT>/campaigns/stack-addmm-a5-107-20260912-opencode/framework/aoa_out/stack_addmm_custom/loop_<run-id>/explore/direction_004/
> 实测：1.1357 x（gate geomean 18.462→16.256us，本 loop 单方向最大增益）；g17 1.332x（P=32，2→32 lane）、g2 1.363x（P=16，4→64 lane）、g20 1.287x，小 P 家族 +1.13~1.29x；g11/g12/g18 仅 1.06~1.09x（其残余是生产/握手而非归并字节，1.25x 证伪阈值命中）；dim=-1 小 case g3 持平、g15 -4.8%（被 stack 带串行链挡住，与本条无关）。输出位等价，精度 22/22 首过、零修复轮。

## 原理

归约维被跨核切分（split-K，见 22 号卡的生产侧扇出）后，**消费侧的归并**若仍按「每个 tile 只由属主核的 2 条 AIV lane 归并」，实际并行度极低：实测 25 个性能门 case 里有 17 个走 split 路径，归并只落在 64 条 lane 中的 2~18 条上，每条 lane 从 GM 读 P×32KB 局部量（P 最大 32），并且 `ProcessV1Tile` 每段一枚 `PipeBarrier<PIPE_ALL>`（最多 P 次/lane）。最后一段之后的归并尾部因此成为串行墙，而 46~62 条 AIV lane 空转。

机制：把归并工作与 tile 属主**解绑**——

1. 每个 tile 的 baseM 行按自适应高度切成条带（S 行，并在尾部钳制，语义同既有 subValidM）；
2. 所有 `(tile t, 条带 r)` 单元展平为一维（`u = t*stripesPerTile + r`），按 `flatIdx` 跨**全部 2*usedCores 条 lane** 派发（`u = flatIdx; u < totalUnits; u += 2*usedCores`）；
3. 每条 lane 对其单元：批量轮询 tile t 的 P 个就绪标志（沿用既有 `WaitSplitsReady`），随后对自己那段 S 行做归并（MTE2 读 P 个局部量条带 + 向量段 + 按序相加 + 精确写出）；
4. 局部量与标志放在全局 GM，任意 lane 可读——无属主约束。

每条 lane 的局部量流量从 `P × baseM × 4B` 降到 `P × S × 128 × 4B`，每 lane 的 `PIPE_ALL` 段数按同一比例下降。

## 性能问题模式（哪些 profiling 信号说明该用）

- split-K 已启用，但归并段的并行度是「每 tile 2 条 lane」这种结构性欠铺：按 `t % usedCores` 之类的属主映射遍历即可确认。
- 归并段单位时间处理的局部量字节远低于该 lane 的搬运能力（`aiv_mte2` 占比中等但耗时长），且尾部有一段「最后生产者的标志之后」的纯串行段。
- 大量 AIV lane 在同一时刻空闲，而少数 lane 上堆着 P×32KB 量级的装载。
- 归并段的屏障密度与分段数同阶（每段一枚全流水屏障）。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **逐元素归并顺序必须保持段升序**：局部量按 K 段升序累加，输出才与 champion 位等价；不得改成树形/两两并行归约顺序（要改顺序必须另做精度论证）。
2. **条带高度自适应且尾部钳制**：S 的选取要让 `nMmBlocks × ceil(baseM/S) ≥ 2×usedCores`（实例取 S≥8 优先），尾条带按 subValidM 语义处理。
3. **标志轮询与可见性契约不得削弱**：沿用既有批量轮询（`WaitSplitsReady`）语义并保持生产侧可见性契约——AIC 标量写 GM 需要按项 64B 独占行 + 立即 `dcci CACHELINE_OUT`，**打包在共享行里的 flag 会被行粒度写回破坏**（AC-037 家族）。
4. **收益形态有边界**：小/中 P case 获益最大（1.13~1.36x）；中 P case 只有 1.06~1.09x（其残余瓶颈是生产/握手，不是归并字节）；被 stack 带串行链（lane 0..nStackTasks-1）挡住的小 case 不受本条影响，可能为负（实测 g15 -4.8%），须按形态门控。
5. **依赖生产侧扇出**：没有 split-K（22 号卡）就没有本条；单核 tile（每 tile 一段）形态下归并无冗余，禁用。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- shape：归约分段数 P 大、每个 tile 的局部量大、输出块数少的 case 收益最大；小 P 家族整体受益。
- dtype：与 dtype 无关（归并是向量段元素级运算）。
- 流水线：`aiv_mte2` + `aiv_scalar`（归并段向量与装载）；对任何「局部量落 GM、由属主核归并」的 split-K 消费侧适用。
- 与 22 号卡配套：22 是生产侧扇出（谁算分段），本条是消费侧摊平（谁来合并）；两者叠加时段的发布/可见性契约要一起复核。
- 与 25 号卡（跨 Lane 两级归约）的分界：25 切分的是**归约轴**（每 lane 产生局部统计后两级合并）在单核内；本条切分的是**归并任务的派发**（跨全部 lane 摊平，含跨核）。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 统计 split-K case 的归并并行度：tile 数 × 每 tile 分配到的 lane 数 vs 可用 lane 总数，确认欠铺倍数。
2. 计算条带高度：由 `nMmBlocks`、usedCores、baseM 反推 S，使条带单元数 ≥ 2×usedCores；尾部条带钳制。
3. 把 `(tile, 条带)` 展平为一维并改派发循环（`u += 2*usedCores`）。
4. 每条 lane 的顺序改为：批量轮询该 tile 的 P 个就绪标志 → 读 P 个局部量条带 → 向量段按段升序累加 → 写出。
5. 复核可见性契约（生产者独占行 + dcci）与标志批量轮询语义；复核每 lane 屏障段数下降比例。
6. 全量精度用例（含 P=1、每 tile 单段、dim=-1 形态）通过后做平衡交替配对，报小 P/中 P/被串行带挡住三组数字。

## LLM 前置问题（应用前必须自问）

1. 归并当前由谁执行？并行度是几条 lane？可用 lane 总数是多少？
2. 局部量与标志放在哪里？任意 lane 都能读吗？
3. 每 lane 的局部量字节与屏障段数是多少？摊平后降到多少？
4. 归并顺序是否必须保持段升序（位等价要求）？
5. 条带高度怎么定？尾部怎么钳制？
6. 哪些形态不受益（中 P、被 stack 带串行链挡住的）？门控条件写清楚了吗？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；派发循环与条带划分的算术逐 case 核对。
- **精度**：全量用例首过、零修复轮（实测 22/22）；**输出与 champion 位等价**。
- **性能**：配对 geomean 超噪声底（实测 1.1357x）；小/中 P case 应看到 1.13~1.36x。
- **零劣化判据**：中 P case ≥1.05x 视为部分受益；被串行带挡住的 case 允许持平（实测 g15 -4.8% 须门控隔离）。
- **回退**：位等价不成立、可见性契约变化、或目标形态（每 tile 单段）时回退属主归并路径。

## 检索卡（短卡）

动作：把 split-K 消费侧归并从 tile 属主解绑：每 tile 的 baseM 行切自适应条带、(tile,条带) 展平后跨全部 2×usedCores lane 派发，段升序累加。
适用：split-K 生产侧已切分、消费侧归并仍按属主核 2 lane 执行、归并尾部成串行墙的算子。
限制：归并须保持段升序（位等价）；可见性契约（64B 独占行+dcci CACHELINE_OUT）不得削弱；stack 带串行链挡住的 case 须门控。
范围：split-K 归约的消费侧归并派发（长归约欠铺）。
检索词：split-K、归并去中心化、行条带、lane 摊平、usedCores、段升序、位等价。
机会：64 lane 仅 2~18 条在归并；每 lane 读 P×32KB 局部量、每段一枚 PIPE_ALL，末段后成串行墙。
代价：小/中 P 外收益有限（中 P 1.06~1.09x）；局部量与标志搬到全局 GM。
