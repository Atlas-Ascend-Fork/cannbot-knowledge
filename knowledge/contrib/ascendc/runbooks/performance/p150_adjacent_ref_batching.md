---
type: Runbook
title: "P150 Playbook: 相邻引用合批（slot-pair batching）摊薄 per-ref 固定成本 落地 SOP"
description: "完整发现记录见 ../../optimizations/evolution_strategies/discovered/disc_x129.md。"
tags:
  - task.optimization
  - topic.attention
  - topic.parallelism
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x129.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p150_adjacent_ref_batching.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P150.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
aliases:
  - P150
---
# P150 Playbook: 相邻引用合批（slot-pair batching）摊薄 per-ref 固定成本 落地 SOP

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 强制流程。完整发现记录见 [../../optimizations/evolution_strategies/discovered/disc_x129.md](../../optimizations/evolution_strategies/discovered/disc_x129.md)。

## Step 1: 取证

```bash
grep -nE "topk|ref|DataCopy" op_kernel/*.cpp op_kernel/*.h op_host/*.cpp op_host/*.h 2>/dev/null | head -50
```


## 背景与判定
一个 query 行要扫 K 个稀疏 block（topk 引用列表），相邻两个引用在数学上完全独立（各自 mask、各自贡献到同一分母）。把相邻两 slot 合成一个 pair 后，每个 stage 的**启动次数**减半而字节数不变：

- QK：一次 `gemm_v0<M=GP, N=2*BS, K=D, transpose_B>`（两页 K 并排进 L0B），省掉一半 FIX_M / M_MTE1 / MTE1_MTE2 / M_FIX 屏障组与 L0B prime。
- fixpipe：一次 `[GP, 2*BS]` fp32 score tile（字节不变、命令数减半）。
- AIV：score ring 读成 `[HB, 2*BS]`（一次 DMA），max/exp/P cast/rowsum 全部 2*BS 宽，屏障组与 vector launch 减半。
- PV：一次 `gemm_v0<K=2*BS>`，两个 slot 累加进同一个 L0C；两个 kL0 step 中，第 1 步的 L1→L0 装载可以盖住第 0 步的 mma。per-slot K=BS 时是单步，无法重叠。

## 适用场景
- 每 ref 字节小，且没有任何单条 pipe 的忙占比接近饱和（多条 pipe 都明显低于饱和，属于 latency/barrier bound 的 workspace）。
- topk / 引用数至少为 2；引用数为 1 时必须回退 per-slot，否则每个 half 都白跑一遍。
- 死 slot 是 topk 列表的后缀 → pair 只有"全活 / 全死 / 混合"三态，混合 pair 每个 task 至多一个。死 half 用"复制活页 + condval=-1 全 mask"处理，P 恰为 0；**不要**留 L1 未初始化，NaN 会污染累加。

## Step 2: 实施
1. **zN/nZ L1 tile 的 C0 block stride = RoundUp16(rows) * 16**。两个 `[BS, D]` 页顺序写在相邻内存**不构成** `[2*BS, D]` tile：第二个页的 column block 会落在错误的元素偏移。必须按"parent tile + 行偏移"写：
   `copy_gm_to_l1_rows<T, parentM, parentN>(dstBase, rowOffset, src, srcRowStride, BS, D)`，
   内部用 `MakeLayout<zN>(parentM, parentN)` 建布局，目标地址取 `dstBase[(rowOffset/16)*256]`。这样 zN `[2*BS, D]` 的写恰好等于 QK 的 nZ `[D, 2*BS]` B 读，也等于 PV 的 zN `[2*BS, D]` B 读。A 侧（P tile, M=16）对 stride 不敏感，普通 `copy_gm_to_l1<GP, 2*BS>` 一次即可。
2. 非转置 B 的 K-tile 偏移 `kL0Idx * ELE_NUM_PER_C0 * kL0Size`（`ELE_NUM_PER_C0=16`）本来就是对的（zN 行块 stride 恒为 256），不要"顺手改成" `kL0Idx * kL0Size * N`。
3. L1 ring 深度按 pair 计：先按 `pair_bytes = 2*(Q + KV + P)` 计算可放 pair 数；提前发车深度应与 per-slot ring 的等效在飞页数比较，避免 UB/L1 超预算。
4. 每个 parity 一个 MTE2→MTE1 flag 的纪律不变；KVP/2 提前发车应维持"每 parity 至多一个未决 flag"。
5. score/P ring 步长改成 `(TOPK+1)` 个 tile，保证奇数 TOPK 的最后一个 pair tile 不跨 ring 槽；host 侧 b1/b2 同步。
6. fixpipe 收窄：`realTailM = (g <= HB ? HB : GP)`。两个 AIV 子块都按整 8 行块读且 `aivWid*HB >= g` 时直接跳过；收窄后每个消费者拿到的仍是"全部写满"的行，不会留下 stale/未初始化 lane。

## Step 4: 边界与回退
- 若某条 pipe 已接近饱和（例如 MTE2 忙占比很高），合批只会增加该 pipe 的排队，收益有限。
- 奇数 TOPK、引用数 1、混合死活 pair 是三个必须单独覆盖的边界。

## Step 3: 验证
- 与 per-slot 参考实现对比：全活、全死、混合 pair、奇数 TOPK、G=1。
- 用逐字节/逐元素对比确认布局没有错位；重点查第二个 half 的 column block。
- 同设备同窗口 A/B，观察 gemm/fixpipe/vector launch 次数是否减半。

## 关联
- 与 [X140](../../optimizations/evolution_strategies/discovered/disc_x140.md)（M 方向合批）同属"减少 task/启动次数"的路线，但本卡合的是 topk 引用维，X140 合的是 M 行。
