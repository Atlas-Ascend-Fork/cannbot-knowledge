---
type: Optimization
title: 稀疏 scatter 读批量化（MTE2 批读连续多 block）+ 逐块 AtomicAdd 背靠背写
description: 把稀疏scatter的逐块GM读取改为批量读取，同时保留按稀疏索引的逐块AtomicAdd写。
tags:
- task.optimization
- topic.attention
- topic.implementation.synchronization
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/05-sparse-scatter-batch-read-atomic-add.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：稀疏 scatter 读批量化（MTE2 批读连续多 block）+ 逐块 AtomicAdd 背靠背写

> **单一优化点：** 当一个 scatter 循环**逐块**地把 GM 源读入片上、再逐块 `AtomicAdd` 写到**稀疏**目的位置（每块 1 笔碎 MTE2 读 + 1 笔 MTE3 AtomicAdd 写 + 一组 per-block 跨管线同步）时，把源在 GM 内**紧凑连续**的多 block 用**一次 `DataCopy` 批读**到片上累加器，再**逐块背靠背** `AtomicAdd` 写到各自稀疏 dst。把"N 笔碎读 + N×同步"塌缩为"1 笔批读 + 逐块背靠背写 + 极少同步"。写仍是稀疏 `AtomicAdd`（不同 block 的 idx 不同，**无法 merge 成一次写**），所以本策略优化的是**读的批量化（MTE2 笔数 N→1）+ 同步开销塌缩（per-block 同步→批末一次）+ 写指令背靠背发填满 MTE3 队列**，而非写的数据量。本策略只改"scatter 阶段的搬运编排（读批量化 + 同步塌缩 + 写背靠背）"，不改数学语义、不改 scale 时机、不改 workspace 布局、不改跨核同步拓扑、不改 cube 侧。
>
> **算子/管线无关性：** 适用于 AscendC 任意"按稀疏索引 scatter 累加（`AtomicAdd`）写"的 Vector 侧循环（MTE2 读 GM→UB、MTE3 `AtomicAdd` 写 UB→GM），只要被批读的源在 GM 内连续紧凑、目的写是稀疏 `AtomicAdd`。不限于任何具体算子。

---

## 1. 原理

gather 批量化（同族策略 04）能把"逐块写"合并成"批量 flush"，是因为 gather 的**目的是连续的**。scatter 的**目的是稀疏的**——不同 block 的 idx 不同，写到不同行，无法用单条 `DataCopyPad` 的 `dstStride` 表达（间距不恒定）。因此本策略：
- **只批量化读**（源连续 → 1 笔批读），不 merge 写（写保持逐块，但背靠背发）。
- **收益来自三处**：读笔数 N→1（MTE2 固定开销下降）、per-block 同步塌缩（scalar/MTE3 等待下降）、写指令背靠背入队填满 MTE3 队列（MTE3 带宽利用率上升）。

本策略利用的硬件机制：

| 机制 | 利用方式 |
|---|---|
| 源连续 → 单次批量 MTE2 | 源在 GM 按 `[blk×blockSize, cols]` 紧凑排布，连续多 block 是一段连续 GM → **一次 `DataCopy` 批读多 block**（替代 N 次小读） |
| MTE3 指令背靠背入队 | 逐块 `AtomicAdd` 写之间**不再插同步**（仅批末一次 `MTE3_MTE2`），不同 dst 的写独立可并行入队、idx 重复同 dst 由 `AtomicAdd` 硬件串行保证正确 → 写指令背靠背发，填满 MTE3 队列 |
| per-block 同步塌缩 | 原每块 3 组同步 → 批末 1 组 `MTE3_MTE2`（释放累加器给下批 MTE2 复用）；批内 flag 链仍保留以保证 MTE2→MTE3 顺序，但开销被多 block 摊薄 |
| `AtomicAdd` 语义不变 | 写路径仍是 `SetAtomicAdd<float>` + `DataCopy(UB→GM)`，跨核同址累加由硬件串行保证正确；本策略只改"读怎么攒、写怎么排" |

定性 pipe 归因（相对）：`aiv_mte3_time`（scatter 写）显著下降——这是本策略的主判据（写背靠背填满 MTE3 队列 + per-block 同步塌缩）；`aiv_scalar_time` 下降（per-block 同步数塌缩）。这是判断本策略是否对症的关键。

---

## 2. 性能问题模式（基线写法）

低效基线在 scatter 阶段逐块做 GM→UB→GM 累加（按稀疏索引把源的 block 写到 workspace 的稀疏位置）：

```text
# 逐块循环（多路各一次 for）
SetAtomicAdd<float>()
for blk in blkStart .. blkEnd:
    idx = topkIndices[blk]                         # 稀疏目的行号（GetValue 标量读）
    tokenStart = idx * blockSize
    # 越界行 clamp（partial last block）...
    DataCopy(acc, gm[src + blk*blockSize*cols], blockSize*cols)   # 1 笔碎 MTE2 读
    SetFlag<MTE2_V>(); WaitFlag<MTE2_V>()
    SetFlag<V_MTE3>(); WaitFlag<V_MTE3>()
    DataCopy(gm[dst + tokenStart*cols], acc, blockSize*cols)      # 1 笔 MTE3 AtomicAdd 写
    SetFlag<MTE3_MTE2>(); WaitFlag<MTE3_MTE2>()                        # 释放累加器给下一块
SetAtomicNone()
```

每个 block 带来：
- **1 笔碎 MTE2 读**：源在 GM 内按 `[blk×blockSize, cols]` **紧凑连续**，但基线逐块各发一条小 `DataCopy`。payload 小时固定开销占比高。
- **1 笔 MTE3 `AtomicAdd` 写**：写是稀疏的（不同 block 的 idx 不同，目的位置分散），**无法 merge**——这是本策略与 gather 批量化（策略 04）的关键区别。
- **3 组 per-block 跨管线同步**：`MTE2_V` + `V_MTE3` + `MTE3_MTE2`，同步开销随 block 数线性堆叠。
- **MTE3 队列未填满**：逐块写之间被同步隔断，写指令无法背靠背入队，MTE3 带宽利用率低。

block 数大（blockSize 小）时，每内层步大量碎 MTE2 读 + 大量 MTE3 写 + 3 倍同步。典型症状：profiling 显示 `aiv_mte3_time` 主导，scatter 循环 block 数巨大、单笔 payload 小。

核心改动：
```text
# BatchScatter 批量化路径（blockSize ≤ 批行数上限）
maxBlksPerBatch = batchRowCap / blockSize                  # bs=1 时一批多块
while blk < blkEnd:
    idx = topkIndices[blk]; tokenStart = idx*blockSize
    if partial(tokenStart+blockSize > s2): flush 当前批; 退回逐块; continue
    if 批满(maxBlksPerBatch): FlushAccumulator()
    idxBatch[count++] = idx; blk++
flush 剩余批

# FlushAccumulator：1 笔批读 + 逐块背靠背写 + 1 组批末同步
rowsInBatch = batchBlkCount * blockSize
DataCopy(acc, gm[srcBase + batchStart*blockSize*cols], rowsInBatch*cols)   # 1 笔批读
SetFlag<MTE2_V>(); WaitFlag<MTE2_V>()            # flag 链保证 MTE2→MTE3 顺序
SetFlag<V_MTE3>(); WaitFlag<V_MTE3>()
for b in 0 .. batchBlkCount:                     # 逐块背靠背 AtomicAdd（无块间同步）
    DataCopy(gm[dstBase + idxBatch[b]*blockSize*cols], acc[b*blockSize*cols], blockSize*cols)
SetFlag<MTE3_MTE2>(); WaitFlag<MTE3_MTE2>()      # 批末释放累加器给下批
```

---

## 3. 正确性红线

### 3.1 AtomicAdd 语义与 dtype
- scatter 入口处 `SetAtomicAdd<float>()`，出口处 `SetAtomicNone()`。`FlushAccumulator` 内的 `DataCopy(dstGm, ...)` 依赖外层已开启的 AtomicAdd，**自身不重复 Set**（重复 Set 可能复位计数）。
- workspace 必须是 **FP32**（硬件 `AtomicAdd` 支持 FP32）；源也是 FP32（如 cube Fixpipe 落地）。
- 背靠背写不同 dst：独立可并行入队；idx 重复同 dst：由 `AtomicAdd` 硬件串行累加保证正确。**无需**软件对同 dst 写加定序。

### 3.2 oob idx → 0
- `idxRaw < 0 || idxRaw >= maxBlock`（`maxBlock = CeilDiv(s2, blockSize)`）→ `idx = 0`（对齐参考实现的越界索引→0 契约语义）。
- 判定在攒批时逐 block 做，oob block 的 `idx=0` 会写到 dst 的 0 行（与基线逐块路径完全一致，精度中性）。

### 3.3 partial last block → s2-1 clamp（界内/越界段）
- partial 判定：`tokenStart + blockSize > s2`（该 block 的尾部行超出 S2）。
- partial block **必须退回逐块**（不能进批）：因为越界部分需把 OOB 行逐行 `AtomicAdd` 到末行偏移 `(s2-1)×cols`（对齐参考实现的 `clamp(max=S2-1)` 语义）。批化路径的背靠背写无法表达"逐行 clamp 到同一末行"。
- 退回前先 `FlushAccumulator` 当前已攒的非 partial 批（保证顺序：已攒批先写完，再处理 partial）。

### 3.4 scale 不在 scatter 乘（单乘归一）
- 若该路输出的 scale 由收尾阶段单乘（`Cast` 时 `Muls(scale)`），scatter 阶段 **不乘 scale**。
- 若在 scatter 乘 scale，会与收尾的 scale 双乘导致 `输出 = scale²`。本策略 `FlushAccumulator` 不含 `Muls`。

### 3.5 同步事件类型与顺序（关键）
- 批内：`MTE2_V`（批读完→V 可见）→ `V_MTE3`（V→MTE3 写）。scatter 阶段无 V 计算时，**flag 链仍保留**——它的作用是保证"MTE2 批读完成 → MTE3 写"的顺序（硬件上 MTE2 和 MTE3 是不同管线，无 flag 不能保证顺序）。删掉 flag 链会导致 MTE3 写到未完成 MTE2 读的累加器。
- 批末：`MTE3_MTE2`（MTE3 写完 → 释放累加器给下批 MTE2 复用）。这是单缓冲跨批复用的 WAR 同步，漏加会踩踏。
- 事件类型必须与管线对匹配：`MTE2_V`（MTE2→V）、`V_MTE3`（V→MTE3）、`MTE3_MTE2`（MTE3→MTE2）。误用会顺序错乱。

### 3.6 数学等价
- 仍是"各 block 的源 `AtomicAdd` 累加到 workspace 的 `idx×blockSize` 行"，只是读改成批量、写改成背靠背。累加值、累加位置、累加顺序（FP32 `AtomicAdd` 硬件串行）全部不变。

### 3.7 已知陷阱（常见）
- **陷阱 A 单缓冲漏加批末 `MTE3_MTE2`（跨批踩踏）**：累加器单缓冲跨批复用，漏加批末 `MTE3_MTE2` → 下一批 MTE2 批读覆写上一批尚未被 MTE3 写完的数据 → 间歇性错值/NaN，常与批数相关（单批不触发，多批偶发）。修复：每批末尾严格 `MTE3_MTE2`。
- **陷阱 B partial 末块漏退回（越界段 clamp 丢失）**：partial 块误走批化路径，OOB 行未 clamp 到末行，而是按 `idx×blockSize + k`（k≥validCount）写到越界/错误行 → 末块含 OOB token 的用例（S2 非 blockSize 整数倍）末行累加值缺失/错位，或 workspace 越界踩踏。修复：攒批循环检测 partial，先 flush 再逐块退回。
- **陷阱 C `AtomicAdd` dtype / Set 时机错**：(A) `SetAtomicAdd<float>` 但 workspace 存低精度 → AtomicAdd 不生效（变普通覆盖写）；(B) 在 `FlushAccumulator` 内部每块重复 `SetAtomicAdd` → 可能复位硬件累加计数。修复：workspace 一律 FP32；`SetAtomicAdd` 只在入口设一次、`SetAtomicNone` 在出口清一次。
- **陷阱 D UB 容量溢出（批读超累加器）**：`maxBlksPerBatch` 算错或 blockSize 上限判定缺失 → 一批总行数 × cols × 4B > 累加器容量 → 编译期 buffer 校验失败或运行时 UB 踩踏。修复：`maxBlksPerBatch = batchRowCap / blockSize`（整除）；blockSize 过大整体退回逐块。
- **陷阱 E 批内 flag 链误删（MTE2→MTE3 顺序失保）**：scatter 阶段无 V 计算时，误以为可删 `MTE2_V/V_MTE3` flag 链 → MTE3 写先于 MTE2 批读完成 → 读到半初始化数据。修复：即使无 V 计算也保留 flag 链（保 MTE2→MTE3 顺序，与是否有 V 计算无关）。
- **陷阱 F blockSize 超限未退回（单 block 超 UB）**：blockSize 超过批行数上限未走退回 → 批读单 block 已超累加器 → UB 越界。修复：函数首部判定 blockSize 超限 → 整体退回逐块。
- **陷阱 G 误把稀疏写当可 merge**：仿照 gather 批量化用单条 `DataCopyPad(dstStride=...)` 合并多 block 写，但 dst 间距不恒定（不同 idx）→ 写出错位/越界、累加到错误行。修复：写保持逐块背靠背 `AtomicAdd`，**不 merge 写**。本策略只批量化读。

---

## 4. 泛化条件

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| scatter 循环形态 | 逐块 `GM→UB→GM(AtomicAdd)`，每块 1 笔碎 MTE2 读 + 1 笔 MTE3 `AtomicAdd` 写 + per-block 同步 |
| 源连续性 | 被批读的多 block 源在 **GM 内紧凑连续**（`src[blk×blockSize×cols]` 紧邻，无 gap/padding）。源不连续（按随机索引 gather 源）→ 不适用（属 gather 范畴，用策略 04） |
| 目的稀疏（`AtomicAdd`） | 写是按索引 scatter 到稀疏 dst，且需累加（`AtomicAdd`）。若目的连续可 merge → 用策略 04 的批量 flush 更优 |
| UB 批容量 | 一批的总行数 × cols × sizeof(T) ≤ 累加器容量。单 block 已超容量（`blockSize > 批行数上限`）→ 退回逐块 |
| dtype 一致 | 源/目/dst 同 dtype（FP32 `AtomicAdd` 场景：源是 cube 落地的 FP32，dst 是 FP32 workspace） |
| 对齐 | 批读起始/长度 32B 对齐；cols 已按 dtype 对齐时天然满足 |
| 基线稳定 | 修改前 build/精度/perf 可重复 |

优先适用：
- block 数大（blockSize 小、topk 大），profiling 显示 `aiv_mte3`（scatter 写）或 `aiv_scalar`（per-block 同步）占比高。
- 源张量（如 cube Fixpipe 落地）在 GM 按 block 紧凑排布，连续多 block 天然连续。
- `AtomicAdd` 写（跨核或同核同址累加）是目的写的本质，无法改成普通连续写。

不适用或需先重构：
- **源不连续**（按稀疏索引取源行）→ 这是 gather，用策略 04。
- **目的连续可 merge**（写到连续 workspace）→ 用策略 04 的批量 flush（读写双批量更优）。
- 单 block 超 UB 批容量且无法缩批 → 退回逐块（保留正确性，无收益但不劣化）。
- 源张量在 GM 非 compact（有 inter-block gap）→ 需先改 cube 落地的 dstStride 使其紧凑（属 layout 重构）。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| **Kernel scatter 函数** | 逐块 `for(blk)` 循环（多路各调逐块函数）→ 多次 `BatchScatter`（每路一次）；`SetAtomicAdd<float>()` 开启与 `SetAtomicNone()` 收尾保留 |
| **新增 `BatchScatter`** | 单路 scatter 编排：blockSize 超限/partial 退回逐块；否则攒批 + `FlushAccumulator` |
| **新增 `FlushAccumulator`** | 一次 `DataCopy` 批读 GM→UB + `MTE2_V/V_MTE3` flag 链 + 逐块背靠背 `AtomicAdd` 写 + 批末 `MTE3_MTE2` |
| Tiling / Host / cube / ws 布局 / 跨核同步 | **不改** |
| 逐块路径 | **保留不动**（作为退回路径，含界内/越界行 OOB clamp） |

### 5.2 maxBlksPerBatch 的取值
`maxBlksPerBatch = batchRowCap / blockSize`（向下取整，≥1）：

| blockSize | maxBlksPerBatch | 一批行数 |
|---|---|---|
| 1 | 批行数上限（如 16） | 16 |
| 8 | 2 | 16 |
| 16 | 1 | 16 |
| 超上限 | — | 退回逐块 |

批大小恒为"凑满累加器容量"，保证 UB 利用率最大、批数最少（同步次数最少）。

### 5.3 退回路径（必须保留）
三种情况退回逐块（保留界内/越界行 clamp 语义）：
1. **blockSize 超批行数上限**：单 block 已超 UB 批容量，整路走逐块。
2. **partial last block**（`tokenStart + blockSize > s2`）：先 `FlushAccumulator` 当前已攒批，再对该 partial block 逐块。
3. **`blkStart >= blkEnd`**：子核无任务，直接返回（`SetAtomicAdd` 已在入口开启、`SetAtomicNone` 在末尾收尾，不会泄漏 atomic 状态）。

### 5.4 数据与缓存布局
- **源布局（GM，连续紧凑）**：源按 `[blk×blockSize, cols]` 紧凑排布，相邻 block 无 gap；连续多 block 是一段连续区间，可用单条 `DataCopy` 一次读。
- **目的布局（GM，稀疏 AtomicAdd）**：workspace 行宽 `cols`（已对齐）；第 blk 个 block 写到 `dstWsBase + idx×blockSize×cols`（idx 稀疏）。不同 block 的 idx 不同 → 位置分散；idx 重复 → `AtomicAdd` 硬件串行累加。
- **片上累加器**：复用既有 plain `TBuf`（非 TQue），单缓冲跨批复用（靠批末 `MTE3_MTE2`）；多路**分时复用**同一累加器（串行调用，不并发），无需为每路单独开 buffer。
- **idxBatch（标量数组）**：栈上小数组（≤批行数上限个），存本批各 block 的 idx，供 `FlushAccumulator` 逐块写时寻址。

---

## 6. LLM 前置问题

| 问题 | 必填内容 |
|---|---|
| scatter 循环形态 | 哪个循环、每块几笔 DataCopy（读+写）、几组 per-block 同步、block 数 N |
| 源连续性 | 源多 block 在 GM 是否紧凑连续（给出 `srcOff = base + blk×blockSize×cols` 证明，无 gap） |
| 目的稀疏性 | 写是否按 idx scatter 到稀疏 dst（不同 block 的 idx 不同）？是否 `AtomicAdd` 累加？ |
| UB 批容量 | 累加器容量？`maxBlksPerBatch` 取值？一批字节核算 ≤ 容量？ |
| 退回路径 | blockSize 上限（超限退回）？partial 末块（`tokenStart+blockSize>s2`）退回？oob idx→0？ |
| 同步 | 批内 `MTE2_V/V_MTE3` flag 链（保 MTE2→MTE3 顺序）、批末 `MTE3_MTE2`（释放累加器）的落点 |
| AtomicAdd | `SetAtomicAdd<float>` 时机（入口一次）、dtype（FP32 workspace）、是否跨核（可见性 barrier） |
| scale | scatter 是否乘 scale？（应否——收尾单乘） |
| 瓶颈定位 | profiling `aiv_mte3`/`aiv_scalar` 占比；确认是逐块碎读 + per-block 同步主导 |
| 基线 | 修改前 build/精度/perf 基线值 |

任一项无法回答，不实施。

---

## 7. 验收标准

```bash
bash <build_script> --soc=<soc> --op=<op>
bash <build_script> --soc=<soc> --op=<op> --wheel
source <set_env>
pytest <op>/test/test_<op>_*.py
```

精度：与基线**逐位一致**（本策略精度中性，只改搬运不改计算）。不得出现任何新 FAIL。

性能（**用 profiling 归因**，相对）：
- **`aiv_mte3_time` 显著下降**（写指令背靠背入队填满 MTE3 队列 + per-block 同步塌缩）——本策略主判据。
- `aiv_scalar_time` 下降（per-block 同步数塌缩：N×3 组 → 批数×3 组）。
- **判据**：`aiv_mte3` + `aiv_scalar` 双降。若 `aiv_mte3` 未降，说明 scatter 写非瓶颈或写已带宽饱和（重新归因）。

边界 shape：
- `blockSize=1`（批量化收益最大，每内层步 block 数最多）、`blockSize` 中等（批大小递减）、`blockSize` 超限（退回逐块路径）。
- S2 非 blockSize 整数倍（触发 partial 末块退回）。
- topk 含 oob idx（`idx<0` 或 `idx>=maxBlock`，验证 idx→0）。
- topk 含重复 idx（验证同 dst `AtomicAdd` 硬件串行）。
- 不同 cols（影响对齐与累加器容量核算）、不同 dtype。

回退或缩小策略的条件：
- 累加器容量不足以容纳一批（且无法缩批/重打包）→ 整体退回逐块。
- 精度失败且无法定位到 `MTE3_MTE2`（陷阱 A）/partial（陷阱 B）/dtype（陷阱 C）/flag 链（陷阱 E）单一原因。
- profiling 显示 `aiv_mte3`/`aiv_scalar` **未下降**——说明 scatter 非瓶颈，或读本就非 op-count 受限（如已是带宽受限），重新归因。
- 源在 GM 非 compact（有 inter-block gap），无法用单条 `DataCopy` 批读 → 需先重构 cube 落地的 dstStride。

与其它策略的关系：与同族策略 04（gather 批量化）**对称**。04 优化 gather 读侧（按稀疏索引读 GM→连续 ws，读写都可批量），本策略优化 scatter 写侧（连续源读 GM→稀疏 dst `AtomicAdd`，只读可批量、写因稀疏无法 merge）。两者可叠加（04 先批量化 gather，本策略再批量化 scatter）。本策略的"写"依赖同族策略 01 建立的"单份共享 FP32 workspace + 跨核 AtomicAdd 直累"机制——01 决定累加目标的布局，本策略决定搬运到该目标的编排（本策略要求 `AtomicAdd` 已正确开启）。独立于策略 02（收尾并行）、03（bf16 matmul）。

## 检索卡（短卡）

动作：把稀疏scatter的逐块GM读取改为批量读取，同时保留按稀疏索引的逐块AtomicAdd写。
适用：scatter循环逐块从GM读入片上，并逐块AtomicAdd到稀疏目的地址。
限制：保持AtomicAdd<float>语义：入口启用、出口恢复非原子状态；稀疏写不能合并为单条dstStride传输。
范围：Kernel scatter函数中写向workspace稀疏位置的路径。
检索词：稀疏scatter、批量读、MTE2、AtomicAdd、DataCopyPad、dstStride。
机会：scatter阶段仍逐块执行GM→UB→GM累加。
