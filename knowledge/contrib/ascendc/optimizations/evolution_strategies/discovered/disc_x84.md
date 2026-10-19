---
type: Optimization
title: "X84: 固定延迟受限内核的「预计算 launch 描述符 + 拆除 AscendC 缓冲框架」"
description: "当 host tiling 保证 taskNum ≤ 物理核数 ⇒ 每核恰好 1 个 task 时，内核里所有\"按任务\"的开销都变成\"按核\"的固定开销，没有任何东西被摊销。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.ordering
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X84: 固定延迟受限内核的「预计算 launch 描述符 + 拆除 AscendC 缓冲框架」

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> id: X84
> origin: discovered
> discovered_round: 4
> discovered_from: round_4/parallel_3
> base_speedup: 1.2709x -> 1.3744x (vs PyTorch; -8.8% kernel time)
> ```

## 核心思路

当 host tiling 保证 **taskNum ≤ 物理核数 ⇒ 每核恰好 1 个 task** 时，内核里所有"按任务"的开销都变成"按核"的固定开销，
没有任何东西被摊销。此时唯一杠杆是把**每核那条固定指令流**本身缩短，而不是调 tile/流水/核数。

三步消除（按收益与安全性排序）：

1. **host 预计算 launch 描述符**：host 侧把每个 block 的最终值（元素偏移、`rowsValid/colsValid`、全部描述符标量）
   打成紧凑记录（本算子：128B/block + 32B/task），device 退化为「读自己那条 cacheline + 发描述符」。
   2 次整数除法、~15 个派生算术、以及 `cPadFlag` 这类分支全部从 device 消失。因为它是 shape 的纯函数，
   直接搭在既有的 per-shape tiling 缓存上 ⇒ 稳态 host/H2D 成本为 0。
2. **拆除 AscendC `TPipe`/`TBuf` 框架**：`TPipe` 的构造函数会做 `ResetPool`，并为本内核根本没用的
   matmul 宏无条件执行 `AllocEventID`/`SetFlag<M_MTE1>`，随后是 `InitBuffer`×N + `TBuf::Get`×N。
   AscendC 的 TBuf 地址是**池内相对偏移、按 InitBuffer 顺序从 0 起**，所以可以用
   `LocalTensor<T>(pos, addr, tileSize)` 在**完全相同的偏移**上重建张量——这是等价替换，不是简化，精度不变。
3. **单任务直线路径**：去掉任务循环，并删掉前导 `PipeBarrier<PIPE_ALL>`（每核 1 个 task 时它只覆盖跨任务的
   缓冲区复用，可证明是 no-op）。

保留一条 legacy strided 路径（`grid>32` / `taskNum>384` / 偏移超 int32 时由 host 选择）作通用兜底。

## 判定信号（先确认再动手）

- host tiling 给出 `taskNum ∈ {1,2,3,4,8,16} ≤ usedCoreNum = min(taskNum, 24)`；
- `aic_scalar_time` 占 `aicore_time` 一半以上，**且与 shape 几乎无关**（同一内核在 16×32×32 与 8×64×128 上都是 ~0.9-1.5us）
  ⇒ 它是"固定指令流"，不是"数据量驱动"；
- 五条 AIC pipe 的 `Σ/aicore_time` 接近 1（近串行，实测 0.938）⇒ 单条 pipe 变快就能 1:1 变现。

## 量化结果（1_BatchMatmul / torch.bmm，Ascend910B2C，全量 51 例）

| 项 | 值 |
|---|---|
| round_3 best（n6，burst 连续性） | 1.2709x vs PyTorch |
| 本策略（x1） | **1.3744x**（两轮独立互斥重测 1.3562 / 1.3927） |
| 同窗交替配对 A/B vs n6 | `geo(asc_B/asc_A)` = 0.9120 / 0.9111；噪声底 0.9944 ⇒ **约 15× 噪声底** |
| 支持面 | 51/51 精度通过，50/51 bit-exact；49/51 例 ≥ 1.0x |
| 残余 pipe 结构 | scalar 48.8% / mte2 24.2%，`Σ5/aicore` 0.938 → 0.841 |

## 适用场景

- 核内 **taskNum ≤ 核数**（每核 1 task）的中小 shape 内核，固定开销主导；
- 设备直编（`<<<>>>` + bisheng `-xasc`）、不依赖 kfc 的自包含内核——若用 MatmulImpl/kfc，框架 prologue 由库拥有，本条第 1/3 步仍可用、第 2 步不可用；
- 与"扩核/扩 tile"路线正交且互斥（后者在本形态无收益）。

## 已证伪的邻域（勿重复）

- `grid ≥ 24` 吃满核；AIV 分流（`KERNEL_TYPE_AIV_ONLY` 自带 ~+1.4us 入口地板）；
  DMA 条数优化（最少/最多 DMA 分别慢 2.9%/32.6%，每 task 2 条描述符已是下界）；
  `P71` IBShare（每核 1 task 无第二消费者）；per-task→per-core 的成员化/句柄外提家族（单迭代循环体 ⇒ 恒等变换）；
  AIC 标量通路上的 64-bit 打包读（实测比 32-bit 慢 2.08%）。

## 来源

自动发现于第 4 轮进化，算子 1_BatchMatmul（TileLang→AscendC 生成核修复，51 例，全部 <9 MFLOP）。
round_1 0.9945x → round_2 1.1962x → round_3 1.2709x → **round_4 1.3744x**。
