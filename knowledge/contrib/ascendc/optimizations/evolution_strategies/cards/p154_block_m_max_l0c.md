---
type: Optimization
title: "P154: 在 L0C 预算内把 block_m 取到最大 16 对齐值"
description: "CV 融合 attention 的每个 KV 迭代有固定条数的 L1→L0 装载、mma、Fixpipe 与跨核 flag，条数与 block_m 无关；当 profiling 显示 AIC scalar/发射是瓶颈而非 MTE2/mac 饱和时，增大 block_m 可用同样指令数多算行，按 1/block_m 降低 task 数、迭代数与每 score 的 K/V 字节。block_m 取 L0C 预算允许的最大 16 对齐值，并为 UB epilogue 留足空间。"
tags:
  - task.optimization
  - topic.memory
  - topic.parallelism
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/discovered/disc_x149.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/9537f7f3304f98a51bb2cfe27d46ea88419c6fa2/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p154_block_m_max_l0c.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/1084df8aaa86b2e7a0ca4e723b4ea4b366cd3eeb/community/ops/ascendc-evolution-strategies/references/preconditions/P154.yaml
    role: constraint
created_at: "2026-11-03T15:14:30Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# P154: 在 L0C 预算内把 block_m 取到最大 16 对齐值

> 证据状态：结构化来源为对应 X 发现记录（固定 commit）；实际算子的正确性/性能验证报告尚待补充。补齐前请把本卡视为待验证晋升，不用于强结论。

> 晋升自 X149（discovered，draft）。详细发现记录见 [../discovered/disc_x149.md](../discovered/disc_x149.md)。

## 核心思想
CV 融合 attention（AIC 出 S / AIV softmax / AIC 出 O）里，一个 KV 迭代的 AIC 侧工作量是固定条数的"L1→L0 装载 + mma 发射 + Fixpipe + 跨核 flag"，**条数与 block_m 无关**（每个 chunk 一次）。因此若 profiling 显示 AIC scalar 是第一瓶颈（而非 MTE2 或 mac 饱和），增大 block_m 等于用同样条数多算行，是纯赚：task 数、迭代数、每个 score 的 K/V 字节都按 1/block_m 下降。

判据（先量化再动手）：
1. `msprof --aic-metrics=PipeUtilization` 采 2–3 个代表 case，看 AIC 的 scalar / mte2 / mac / fixpipe 占比。若 scalar 最高（而 mte2、mac 明显较低），则环是标量/发射受限。
2. 此时"实测每迭代时间与字节账严格吻合"是**假象**——标量开销 ∝ 指令条数 ∝ 字节，两者会同时线性变化。

## 适用场景
- O 常驻 L0C 的设计（例如 X126 一类）：L0C 同时放 acc_s 与全部 acc_o，预算为
  `block_m * (BLOCK_N_BASE + dim_align) * sizeof(acc) <= L0C 容量`。
- block_m 取满足上式的最大 **16 对齐**值；D 越大，可用的 block_m 越小。
- 反例：若 mac 或 MTE2 已接近饱和，加 block_m 只会加剧该 pipe 的排队；若 UB 容不下 epilogue 的 `bm2 * dim_align * sizeof(acc)` 整块暂存，必须走 dim_split 分片 epilogue（该路径要另行验证）。

## 关键修改点
1. host 侧 Derive 与 kernel 的 m_budget 分档同步改，并重算 s_blks / task 数 / workspace 尺寸。
2. 所有**硬编码缓冲偏移**改成按 block_m 派生（例如 acc_o_l0c、p_l0 的固定偏移）；`lhs_resident` 一类判据从固定字节数改成"Q + P 总占用不超过预算"。
3. 提高 block_m 会让 `bm2 = block_m/2` 越过某些运行期 predicate 的隐式假设，可能把休眠的 dim_split epilogue 分支翻成 true。**必须显式关闭未验证分支**，并重新核对 UB 总量（mask scratch、暂存缓冲等都要计入）。
4. 收益按 D 档分别看：D 大的档位通常收益最明显，D 小的档位可能不受影响；decode 等 task 数少的 shape 可能因固定成本占比高而退化。

## 常见陷阱
- block_m 上限由 L0C 容量与 UB epilogue 共同决定，不是越大越好。
- 若增加 block_m 后 UB 超预算，先回收可复用的 scratch（例如 mask 缓冲），再考虑 dim_split；未验证的 dim_split 分支不要直接打开。

## 验证方法
- 静态断言/日志检查 L0C 与 UB 占用。
- 按 D 档、task 数分档做同设备 A/B；重点看 decode 小 case。
- 精度：block_m 改变不应改变数学语义，但 dim_split 分支若被触发必须逐 case 验证。

## 关联策略
- 与 [X145](../discovered/disc_x145.md)（L0B 双槽）正交，可叠加。
- 与 [X126](../discovered/disc_x126.md)（L0C 跨 chunk 累加）共享 L0C 预算分析。
