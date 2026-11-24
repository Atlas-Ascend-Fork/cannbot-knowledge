---
type: Optimization
title: Cube 手写 Matmul 的双层循环重排 — 操作数 L1 复用
description: 交换双层循环；外层操作数仅装载一次并延迟释放，供内层迭代复用。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/07-cube-loop-reorder-for-l1-operand-reuse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Cube 手写 Matmul 的双层循环重排 — 操作数 L1 复用

> **单一优化点：** 在由手工 `LoadData`(GM→L1) + `LoadData`(L1→L0) + `Mmad` 驱动的 AscendC Cube 矩阵乘中，当两个操作数分别随不同维度的循环变化（一个随 M 行块变化、一个随 N/KV 行块变化）时，把**迭代次数更少**的那个循环放到**外层**，让随该循环变化的操作数在 L1 装载一次后、被内层所有迭代复用。等价地：让"被复用次数更多"的操作数放到迭代次数更少的外层，以最小化总 GM→L1 搬运量。
>
> **关键约束（与"多 tile L0C 并行累加"的区别）：** 本策略仅做循环层序重排（M 外 / N 内，或反之），**不改变 L0C 结构、不增加 L0C tile 数目、不改变每对 (M,N) 的独立 Fixpipe 语义**。因此它适用于"每个 (M,N) 块独立累加并立即 Fixpipe"的 Mmad 模式（如 `Q×K^T` 类逐对独立累加天然满足），而**不适用于**需要多个 N 子块在 K 推进中并行累加的模式（如 `P×V` 中 V 复用需多 tile L0C——属另一策略）。

本策略只改"外层内层的循环顺序"和"被复用操作数的 TQue slot 跨迭代持有"。不改变 L0C/Fixpipe 语义、不增加 L0C tile、不引入手工事件同步或软流水。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

手写 Cube matmul 的两个操作数各随一个维度的循环而变化：

```text
# 基线（以 Q×K^T 为例）
for nBlock in N:            # 随 nBlock 变化：K(nBlock, K_dim)
  load K[nBlock_rows, K_dim] from GM → L1       # K 装载在外层，复用内层
  for mBlock in M:          # 随 mBlock 变化：Q(mBlock, K_dim)
    load Q[mBlock_rows, K_dim] from GM → L1     # Q 在内层，每个 (n,m) 对都重装！
    for kTile in K_dim:
      LoadData A[Q mBlock, kTile] L1 → L0A
      LoadData B[K nBlock, kTile]^T L1 → L0B
      Mmad(k=kTile) into L0C[mBlock, nBlock]
    Fixpipe L0C → GM
```

总 operand 装载次数：

```text
若外层循环迭代 N_out 次、内层 N_in 次（均为实际迭代次数，忽略维度具体含义），
"外层操作数"装载 N_out 次（每次内层复用），"内层操作数"装载 N_out × N_in 次。
总 = N_out + N_out×N_in = N_out×(1+N_in)
```

重排"小循环在外、大循环在内"则总 = min(N_out,N_in)×(1+max(N_out,N_in))。差 = |N_out − N_in|。因此**把迭代次数更少的循环放外层**能使总装载次数最小化——外层的操作数装载次数少，内层的操作数装载次数多但被外层乘数放大，所以要"小 × 大"模式。

典型症状：profiling 显示 `aic_mte2`（cube GM→L1）占比高，且其中某操作数的 GM→L1 重装次数与某维迭代数的乘积可观察。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| L1 TQue 跨迭代持有 | 外层的操作数 AllocTensor→Load→EnQue→DeQue 一次，**FreeTensor 推迟到内层循环结束后**，L1 slot 不被释放，内层多次 MTE1 读可复用同一 slot |
| 单次 MTE2→MTE1 同步 | EnQue/DeQue 自动插入的 MTE2→MTE1 同步只做一次，之后内层多次 MTE1 读在同一同步之后，无需再同步（TQue DeQue 后数据稳定） |
| 单 L0C tile 即可 | 每对 (M,N) 独立 L0C→Fixpipe，不要求多个 N 子块并行累加 |

核心改动只是交换两个循环并移动 AllocTensor 和 FreeTensor：

```text
for outerLoop (迭代次数少的维度):
    operand_outer = AllocTensor(); Load; EnQue(MTE2 done); DeQue(MTE1 can read)
    for innerLoop (迭代次数多的维度):
        operand_inner = AllocTensor(); Load; EnQue; DeQue
        for kTile: LoadData L1→L0A/L0B; Mmad(k=kTile)
        Fixpipe L0C → GM
        FreeTensor(operand_inner)
    FreeTensor(operand_outer)
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 计算形态 | 手写 Cube matmul（LoadData+Mmad），存在两个可变操作数分别随 M 行块维度和 N/KV 行块维度的双层循环 |
| 迭代数差异 | 两个维度的循环迭代次数**不相等**（否则重排无收益） |
| L0C 独立 | 每对 (M,N) 产生独立 L0C 结果并立即 Fixpipe，**不需要**多个 N 子块在 K 推进中并行累加（如需并行→属多 tile L0C 策略） |
| TQue 容量 | 外层操作数的 TQue buffer 深度 ≥ 1（单槽即可），被 hold 期间不会有该 TQue 的额外 AllocTensor（通常同一 matmul 阶段只有一个同类操作数） |
| 同步 | 内层多次 MTE1 读仅需外层的一次 EnQue/DeQue → MTE2→MTE1 同步；无需额外同步 |
| 数值一致 | 循环重排不改变每对 (M,N) 的计算，仅改变执行顺序——Fixpipe 按同样的 (M,N) 偏移写入同一 GM 位置 |

优先适用：

- profiling 显示 `aic_mte2`(cube GM→L1) 占比高，其中一个操作数重装次数明显偏多。
- 两维迭代次数明显不等（如一维 ≤4 而另一维 ≥8）。
- 复用维度在 L1 中数据稳定、不与内层同 buffer 的使用冲突。

不适用或需先重构：

- 两层迭代数相等（无收益）。
- 复用操作数的 L0C 累加需要跨内层迭代并行（如 `P×V` 中 V 复用需多个 N 子块同时累加）→ 需多 tile L0C 先行，不能用本策略。
- 复用操作数的 TQue buffer 深度不足，或被同一阶段的其他用途竞争 → 需 TBuf + 手工事件（属手工流水线策略）。
- 数据生产方（另一次 matmul 阶段）依赖原循环顺序产生的 GM 尾同步等——本策略不改变跨核同步位置，但要确认尾同步仍在正确位置。

---

## 3. 迭代次数比较与层序选择

### 3.1 通用规则

```text
count_M = ceil(total_M_rows / M_tile_rows)     # 左矩阵 M 维迭代数
count_N = ceil(total_N_rows / N_tile_rows)     # 右矩阵 N/KV 维迭代数

if count_M < count_N:
    M_outer, N_inner   # Q(M) 装载 count_M 次，K(N) 装载 count_M×count_N 次
else:
    N_outer, M_inner   # K(N) 装载 count_N 次，Q(M) 装载 count_M×count_N 次

# 总 = min(count_M, count_N) + count_M × count_N — 两者相同（交换律），但小循环在外时被加载次数少的操作数在外，
# 大循环在内但被载荷乘数放大 → net 节省 = |count_M − count_N| 次外层操作数装载
```

---

## 4. 实施步骤

### 4.1 修改位置

| 位置 | 修改 |
|---|---|
| 目标 matmul 函数 | 交换外层内层 for 循环；把外层的 AllocTensor+Load+EnQue+DeQue 提到外层 for 体首，FreeTensor 推迟到内层 for 结束之后；内层操作数的 AllocTensor/FreeTensor 入内层 for 体 |
| L0C/Fixpipe | 移到内层 for 体内（每对 (M,N) 一个 L0C） |
| 注释 | 更新循环层序注释，标注"外层迭代数 ≤ 内层迭代数 ⇒ 外层操作数复用" |

### 4.2 伪代码

```text
# 基线
for n in N:
    load K(n)
    for m in M:
        load Q(m)           # Q 每个 (n,m) 对都重装
        for kTile: Mmad
        Fixpipe; FreeTensor(Q)
    FreeTensor(K)

# 重排后
for m in M:                  # M 迭代数 ≤ N 迭代数 ⇒ 放外层
    load Q(m)                # Q 整个 m 内跨 n 复用，不重装
    for n in N:
        load K(n)
        for kTile: Mmad
        Fixpipe; FreeTensor(K)
    FreeTensor(Q)            # Q 在内层全部结束后才释放
```

### 4.3 TQue 跨迭代持有要点

- 外层的 `AllocTensor` → `LoadData`（MTE2）→ `EnQue`（信号 MTE2 完）→ `DeQue`（等 MTE2 完，MTE1 可读）→ 内层循环内多次 MTE1 读 → `FreeTensor`（内层全部结束后）。
- `DeQue` 后 TQue 认为槽位 "被计算方消费中"，**不限制**DeQue 与 FreeTensor 之间的读次数；TQue depth 允许 1 个槽长期被持。
- 内层无该操作数的新 AllocTensor，故不竞争该 TQue 的其他槽位。

---

## 5. 正确性红线

### 5.1 TQue slot 跨迭代持有

- `DeQue` 后数据在 L1 中稳定（MTE2 已完成写入，不会被后续 MTE2 操作意外覆写——外层的 MTE2 只有那一次 Load）。
- 内层多次 MTE1 读**无需**额外同步；EnQue/DeQue 插入的一次 MTE2→MTE1 已足够。
- **不要在内层循环内 FreeTensor + 再 AllocTensor 同一个外层操作数**——这将是重装，恰是本策略要消除的。

### 5.2 数值语义不变

- 每对 (M,N) 的行/列对齐参数、累加初始值（`cmatrixInitVal`）、K-tile 循环、Fixpipe 均不变，仅执行顺序改变。
- Fixpipe 写 GM 偏移不依赖循环顺序——只要 (M 块起点, N 块起点) 对相同，结果相同。

### 5.3 跨核尾同步不变

- 尾同步（如 `CrossCoreSetFlag` 通知向量核）仍在所有循环结束后执行，不因循环顺序改变。

### 5.4 精度与数值顺序

- K 归约的加法结合顺序不变（K 维 Mmad 累加在单 L0C 内进行，累加顺序由 K-tile 循环决定，与 M/N 层序无关）。
- M/N 层序只影响哪个 (M,N) 先算，不影响每个 (M,N) 内部的数值。

---

## 6. 已知陷阱

### 陷阱 1：内存层序误判——外层操作数在内层被意外复用或覆写

问题：外层操作数被内层的同名 TQue 操作误覆盖（如内层有同名 buf 的 AllocTensor）。
症状：外层操作数数据被覆写，Mmad 读到错误的左矩阵，mismatch。
修复：确认外层的操作数使用独立 TQue/TBuf，内层不分配同 buffer 的槽（外层操作数只在外层 AllocTensor 一次，内层只分配另一操作数的槽，不冲突）。

### 陷阱 2：内层迭代数反而更少，重排反向降效

问题：未正确比较 M/N 维度迭代次数，把大循环放外层导致操作数装载反而增多。
症状：性能劣化。
修复：先计算两维迭代次数，确保外层迭代数 ≤ 内层迭代数（§3）；相等时不做。

### 陷阱 3：FreeTensor 在外层循环体首部导致空槽死锁

问题：在外层循环首部对操作数执行 FreeTensor（试图释放上轮槽位），但首轮无上轮，或释放后立即 AllocTensor 导致 TQue 槽位竞争。
修复：外层的 AllocTensor 在外层 for 体首（Alloc→Load→EnQue→DeQue），FreeTensor 在内层 for 体结束后，不使用跨轮复用同一个槽。

### 陷阱 4：尾同步误放到外层循环内

问题：尾同步（`CrossCoreSetFlag`）被误放入外层 for 体内，每外层迭代就发一次，导致计数不配平。
症状：死锁或下游收到错误同步。
修复：尾同步放在所有循环的**最外层**之外（不受循环层序影响）。

### 陷阱 5：误当本策略需要多 tile L0C

问题：担心循环重排会破坏 L0C 累加语义，试图同时引入多 tile L0C。
澄清：本策略适用的模式里每个 (M,N) 对独立 L0C+Fixpipe，重排不影响这个语义。只有需要"N 子块并行累加 + K 复用"的模式（如 `P×V` 中 V 复用）才需要多 tile L0C——那是另一个策略。不要把本策略和"多 tile L0C 并行累加"混在一起。

---

## 7. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 当前循环层序 | M 外 N 内 or N 外 M 内；M/N 维迭代次数各多少 |
| 每个操作数的 GM→L1 装载位置 | 哪个操作数在外层装载（被复用）、哪个在内层（每对被加载） |
| L0C 结构 | 每个 (M,N) 对是否独立 L0C+Fixpipe（确认不需要并行 N 子块累加） |
| TQue 容量 | 外层的 TQue 深度；hold 期间是否有冲突 |
| 数值等价 | 层序重排后每个 (M,N) 对的计算是否不变（行/列对齐参数/累加初始值/Fixpipe 目标偏移是否不受层序影响） |
| 尾同步位置 | 跨核 Set/Wait 是否仍在所有循环外 |
| 基线可重复 | 修改前 build/精度/性能基线 |

任一项无法回答，不实施本策略。

---

## 8. 禁止事项与回退条件

禁止：

- 在外层循环内重复 FreeTensor+AllocTensor 同一操作数（消除重用）。
- 把大循环放外层（陷阱 2）。
- 改变 L0C/Fixpipe `(M,N)` 语义——本策略只重排层序，不增加 L0C tile。
- 在同一轮混入多 tile L0C、手工事件同步、软流水、buf 深度调整或新的 matmul helper。
- 改变跨核尾同步位置（陷阱 4）。
- 对无迭代数差的场景强制重排。

回退或缩小策略的条件：

- 两维迭代数相等 → 无收益。
- 精度失败且无法定位到 TQue 槽位覆写（陷阱 1）/尾同步（陷阱 4）单一原因。
- profiling 显示 `aic_mte2` 未下降 → 该 matmul 阶段非 MTE2 受限或层序重排未生效。
- 需要依赖多 tile L0C 才成立（如 `P×V` 中 V 复用）→ 本策略不适用，改用多 tile L0C 策略。

---

## 9. 验收标准

最小验证：

```bash
bash build --soc=<soc> --op=<op>
bash build --soc=<soc> --op=<op> --wheel
source <set_env> && pytest <op>/test/test_<op>_*.py
```

精度：与基线一致（全部用例通过）。每对 (M,N) 的计算不变，循环层序不影响数值。

性能（profiling 归因）：

- `aic_mte2`(cube GM→L1) 应明显下降。
- 整体 `Task Duration` 在 cube 处于关键路径时不劣化且应下降。
- 若整体持平但 `aic_mte2` 下降 → bottleneck 已转移到其他侧（如 Vector），策略对 Cube 已生效。

边界 shape：M/N 二维迭代数差异明显、差异极小或相等（无收益边界）、单维单迭代（极端）。

结论须写清：

```text
本策略收益相对"M 内/N 外"或"N 内/M 外"原基线；判据是 aic_mte2 下降（操作数重装减少）。
不改变 L0C 结构，也不引入多 tile 并行累加。需要"N 子块并行累加"的模式属另一策略。
```

## 检索卡（短卡）

动作：交换双层循环；外层操作数仅装载一次并延迟释放，供内层迭代复用。
适用：手写 Cube matmul，两个操作数分别随不同循环维度变化。
限制：外层L1操作数的FreeTensor须推迟到内层循环结束后。
范围：手写 Cube matmul 的双层循环与 L1 操作数。
检索词：LoadData、Mmad、L1 TQue、跨迭代持有、循环重排。
机会：双层循环中两个操作数各随一个维度变化。
