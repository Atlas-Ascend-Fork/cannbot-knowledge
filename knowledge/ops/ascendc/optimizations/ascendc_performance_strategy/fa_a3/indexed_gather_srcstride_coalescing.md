---
type: Optimization
title: 索引 gather 的相邻升序读合并（逐行 blockCount=1 → 单条 blockCount=N + srcStride）
description: 把逐行单块 DataCopyPad 改为以 blockCount+srcStride 一次搬运多个源块。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/08-indexed-gather-srcstride-coalescing.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：索引 gather 的相邻升序读合并（逐行 blockCount=1 → 单条 blockCount=N + srcStride）

> **单一优化点：** 当一个索引/sparse gather 循环按**运行时索引**逐行 `DataCopyPad`（每行 `blockCount=1`、源地址随索引跳变）把 GM 数据读入片上 buffer 时，把**源索引升序相邻**的若干行合并为**一条** `DataCopyPad(blockCount=N, srcStride=行间隔字节)`：一次指令搬 N 个 token，源侧用 `srcStride` 跨过 token 间的 GM 间隔。降低 gather 读的**指令数**（及其 issue/scalar 开销），不改变搬运总字节。
>
> **算子/管线无关性：** 适用于 AscendC 任意管线的索引 gather 读（Vector MTE2、Cube MTE2/MTE1），只要被合并的相邻行满足"源索引升序、目的槽位连续"。不限于 FlashAttention；任何 sparse/topK/indirect gather 都可套用。
>
> **与策略 02/03 的区别：** 02 要求源**物理连续**（一条 copy 覆盖整段，省指令**也省访存事务**），并在 §5.3 明确"按运行时索引的随机 gather 必须保持逐元素"；本策略正是补这个缺口——**随机 gather 里相邻两行若源索引升序，可用 srcStride 合并**（省指令、不省访存事务）。03 把逐行 gather/scatter 中转塌缩为"累加器批量 + 单条跨步 scatter"，但其内层 gather 仍是 N 条 `blockCount=1`；本策略嵌在 03 内层 gather 里，把 N 条读再压成 ⌈N/2⌉~⌈N/run⌉ 条。三者互补：连续用 02，gather 中转用 03，gather 读指令再压缩用本策略（依赖 03 提供的连续累加器，`dstStride=0`）。

本策略只合并"索引 gather 中相邻升序行的读指令"。不改变 gather 的值/有效性规则/数据语义、不改 tiling 外层结构、不改跨核同步、不改累加器布局、不引入软流水或新管线。被合并的相邻行非升序（降序/相等）或其一无效时退化为逐行，不在本策略的合并范围。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

低效基线在索引 gather 里逐行各发一条 `DataCopyPad`（典型如按 sparse/topK 索引取 KV 行到片上累加器）：

```text
for j in 0 .. batchN:                                   # 源按 idx_j 跳变
    idx_j = idxUb.GetValue(...)                         # 索引（常已由策略02批量预取到UB）
    DataCopyPad acc[j*rowLen], gm[(base+idx_j)*rowLen],
                {blockCount=1, blockLen=rowLenB, srcStride=0, dstStride=0}
```

每个 token 一条读，带来：

- **读指令数 × N**：`DataCopyPad` 条数随 token 数线性增长，每条有 issue/地址构造/完成固定开销；token 行长固定，**总搬运字节不变**，纯属"指令条数税"。
- **scalar issue 开销放大**：每条读的 `DataCopyExtParams` 构造、地址计算走 scalar 单元；N 大时 `aiv_scalar`/`aic_scalar` 随之堆叠。
- **MTE2/MTE1 issue 槽位浪费**：每条 `blockCount=1` 指令的 payload 远小于一个 issue 槽位能表达的量（`blockCount` 可达数十）。

典型症状：profiling 显示该 gather 所在管线时间（`aiv_mte2`/`aic_mte2`/`aic_mte1`）与 `*_scalar_time` 占比高，且循环次数大、单条 `blockCount=1`；但**有效带宽远低于 HBM 峰值**，说明 gather 是**指令/延迟受限**而非带宽受限——正是"减指令数能见效"的信号。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| `DataCopyPad` 多块搬运 | `blockCount + srcStride` 一次指令搬 N 个源块，源侧用 `srcStride` 跨过块间 GM 间隔；指令条数 `N → ⌈N/run⌉` |
| srcStride 语义 | `srcStride` = 相邻源块**间隔**（前块尾→后块头，字节）；总跨步 = `blockLen + srcStride`。升序相邻行天然可算出合法非负 stride |
| 连续累加器目的（由策略 03 提供） | 目的槽位 j、j+1 在 UB 内连续 ⇒ `dstStride=0`，N 块紧凑写入，无需为目的跨步额外寻址 |
| 计算流水 / 核间协作 | 沿用既有 TQue/累加器同步（03 的 WAR/RAW），不改变流水与协议 |

核心改动（以**相邻两行配对**为最简形态）：

```text
# 基线：每 token 一条读
for j in 0 .. batchN step 1:
    DataCopyPad acc[j*rowLen], gm[(base+idx_j)*rowLen], {blockCount=1, ...}

# 改写：相邻升序 token 对合并成一条 blockCount=2
j = 0
while j < batchN:
    if j+1 < batchN and valid(j) and valid(j+1) and idx_j < idx_{j+1}:
        gapRows = idx_{j+1} - idx_j                     # >=1（升序保证）
        srcStrideB = (gapRows - 1) * rowLenB            # 连续相邻 token ⇒ 0
        if 0 <= srcStrideB < STRIDE_MAX:
            DataCopyPad acc[j*rowLen], gm[(base+idx_j)*rowLen],
                        {blockCount=2, blockLen=rowLenB, srcStride=srcStrideB, dstStride=0}
            j += 2; continue
    # 退化：降序/相等/无效/stride溢出 → 单 token
    DataCopyPad acc[j*rowLen], gm[(base+safeIdx_j)*rowLen], {blockCount=1, ...}
    j += 1
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 搬运形态 | 索引/sparse gather 循环，每行一条 `DataCopyPad(blockCount=1)`，源地址随运行时索引跳变 |
| 目的连续性 | 被合并的相邻行写入**连续**目的槽位（`acc[j*rowLen]`、`acc[(j+1)*rowLen]` 相邻无 gap，即 `dstStride=0`）——通常由策略 03 的紧凑累加器提供 |
| 源升序 | 被合并的相邻行源索引满足 `idx_j < idx_{j+1}`（⇒ `gapRows>=1` ⇒ `srcStride>=0`）；升序是**正确性硬约束**，非优化（见 §6.1） |
| 均有效 | 被合并的所有行索引均有效（`0 <= idx < 源行数`）；含无效行（-1/越界）的对退化为逐行（保持 clamp/skip 语义） |
| dtype/行长一致 | 被合并行同 dtype、同行长（同 `blockLen`） |
| stride 不溢出 | `srcStrideB ∈ [0, STRIDE_MAX)`（`DataCopyExtParams.srcStride` 字段上限，910B 用 `INT32_MAX` 兜底） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- **源索引升序**（sparse/topK 索引常 `sort()` 后升序、`-1` 在尾）→ 绝大多数相邻对可合并，指令数近似减半。
- gather 行数大、单行 `blockCount=1`，profiling 显示该管线 `*_scalar`/`*_mte2`（或 cube 对应）占比高、有效带宽远低于峰值（指令/延迟受限）。
- 索引存在长连续/等差游程（如升序且常出现 `idx, idx+1, idx+2…`）→ 可用 §3.2 的 run-length 把整段压成一条 `blockCount=N`。

不适用或需先重构：

- gather 行**逐行写跨步目的**（`dstStride≠0`、目的非连续）且无紧凑累加器 → 先上策略 03 把 gather 收敛到连续累加器，再用本策略。
- 源索引**恒降序**（如 topK 降序输出）→ 相邻对不满足升序，几乎无法合并；需先在外层把索引升序化（属排序/布局改动，非本策略）。
- 单次 gather 只取 1 个元素/极短行，`blockCount=N` 的 issue 节省不显著。
- 收益主要来自带宽（gather 已带宽饱和，`*_mte2` 不随指令数下降）或算力——非本策略（见陷阱 6/§10）。
- 整体瓶颈在另一侧（如 Cube），gather 已非关键路径——本策略只降 gather 读工作量，**不保证**整体提速（见 §10）。

---

## 3. 合并粒度与 stride 推导

### 3.1 srcStride 推导（通用）

记 `rowLen` = 每行元素数，`rowLenB = rowLen * sizeof(T)`，`base` = 本 batch 的 GM 行基址。

```text
block j  源起 = (base + idx_j)   * rowLen        (元素)
block j+1源起 = (base + idx_{j+1}) * rowLen
srcStrideB = (block_{j+1}源起 - block_j源起) * sizeof(T) - rowLenB
           = (idx_{j+1} - idx_j - 1) * rowLenB
           = (gapRows - 1) * rowLenB            # gapRows = idx_{j+1} - idx_j >= 1
# 连续相邻 token（gapRows=1）⇒ srcStrideB = 0
# block_{j+1}源起 = block_j源起 + blockLen + srcStrideB   ✓ 与 DataCopyPad 语义一致
```

目的侧（连续累加器）：`block j → acc[j*rowLen]`，`dstStride=0` ⇒ `block_{j+1} → acc[(j+1)*rowLen]` 紧邻写入。

### 3.2 两种合并粒度

| 粒度 | blockCount | 适用 | stride |
|---|---|---|---|
| **配对（pair）** | 2 | 任意升序相邻对（含非均匀间隔） | 每对独立 `srcStride`；最简、最通用 |
| **游程（run）** | N | 极大升序游程且**间隔均匀**（`idx, idx+g, idx+2g, …`，含连续 `g=1`） | 整段一个 `srcStride=(g-1)*rowLenB`；连续游程 `srcStride=0` |

- **配对**最通用：不要求间隔均匀，每个相邻升序对各自算 stride 即可，覆盖非连续的升序 sparse 索引。指令数 `N → ⌈N/2⌉`。
- **游程**收益更大（一段压成一条），但要求游程内间隔恒定（一条指令只有一个 `srcStride`）；典型用于**连续游程**（`srcStride=0`，等价于一段连续读）。实现需在线扫描极大均匀间隔游程，复杂度高于配对。
- 默认采用**配对**（`blockCount=2`）；游程作为可选增强，仅在确有长连续游程时启用。

### 3.3 选择规则

```text
默认用配对（blockCount=2）：
  对每个相邻对 (j, j+1)：
    若 valid(j) && valid(j+1) && idx_j < idx_{j+1} && stride合法 ⇒ 合并（j+=2）
    否则 ⇒ 单 token（j+=1），下一轮重新尝试以 j 为起点配对
（单数尾行/降序对/无效对自然落回单 token，无需特殊分支）
可选游程增强（仅当索引常出现长连续/等差段）：
  在配对基础上，先扫描极大均匀间隔游程 [j, j+k)，用 blockCount=k+1 一次搬整段
```

升序判定可由 `srcStride>=0` 隐式蕴含（`gapRows>=1`），但显式 `idx_j < idx_{j+1}` 更清晰、避免计算负 `gapRows`。

---

## 4. 数据与缓存布局

### 4.1 目的：连续累加器（依赖策略 03）

- 合并写要求目的槽位连续（`dstStride=0`）：`acc` 为 plain `TBuf`，槽位 j 偏移 `j*rowLen`，相邻行无 gap。
- 该连续累加器正是策略 03 的批量 gather 累加器；本策略在其内层 gather 上做读合并，**不改累加器布局、不改 03 的 WAR/RAW 同步**。
- 若当前 gather 直写跨步 GM（无累加器），先上 03 建连续累加器，再叠本策略。

### 4.2 源：升序 GM 行

- 源为 `[base .. base+s2Size) × rowLen` 的 GM 行区；合并块的源起满足升序（`idx_j < idx_{j+1}`），`srcStride` 跨过 token 间间隔。
- 源跨段（同一行由多个物理分离的数据段拼成、不同段不同 GM 区/不同行长）→ 各段**独立**做读合并（每段用各自的 `rowLen`），不要跨段合并。

### 4.3 容量核算

```text
合并不改累加器容量（仍 BATCH 行 × rowLen × sizeof(T)，与 03 相同）。
单条 DataCopyPad 的 blockCount 上限：DataCopyExtParams.blockCount 通常 uint16；
  blockLen = rowLenB 须 32B 对齐（行长常为 32B 倍数）。
srcStrideB 须为 32B 倍数（行间隔 × 行长，行长 32B 对齐时天然满足）。
```

---

## 5. 实施步骤

### 5.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| gather 所在 kernel 函数（通常 03 的内层 gather 循环） | 把 `for j: DataCopyPad(blockCount=1)` 改为 `while j` 配对合并 + 单 token 退化；多段源各自合并 |
| Tiling / Host / 跨核同步 / 累加器布局 / 其他阶段 | **不改** |

### 5.2 配对合并 gather 主循环（通用形态）

```text
acc = accBuf.Get<T>()                       # 03 的连续累加器（dstStride=0）
j = 0
while j < batchN:
    merged = false
    if j + 1 < batchN:
        idx0 = idxUb.GetValue(intraBase + globalRow(j))
        idx1 = idxUb.GetValue(intraBase + globalRow(j+1))
        v0 = (idx0 >= 0 && idx0 < srcRows); v1 = (idx1 >= 0 && idx1 < srcRows)
        if v0 && v1:                         # 两行均有效
            gap = idx1 - idx0
            strideB = (gap - 1) * rowLenB
            if strideB >= 0 && strideB < STRIDE_MAX:        # 升序 + 不溢出
                DataCopyPad acc[j*rowLen], gm[(base+idx0)*rowLen],
                            {blockCount=2, blockLen=rowLenB, srcStride=strideB, dstStride=0}
                j += 2; merged = true
    if merged: continue
    # 退化：单 token（含 -1/越界 clamp、降序/相等/溢出对）
    idx = idxUb.GetValue(intraBase + globalRow(j))
    v = (idx >= 0 && idx < srcRows)
    if 慢路径 && !v: ++j; continue            # 无效槽位保留批首 Duplicate(0) 清零
    safeIdx = v ? idx : 0
    DataCopyPad acc[j*rowLen], gm[(base+safeIdx)*rowLen], {blockCount=1, blockLen=rowLenB, ...}
    ++j
# 之后沿用 03：SetWaitFlag<MTE2_MTE3> + 单条跨步 scatter（不改）
```

要点：

- `globalRow(j) = subBlockStride + (chunkStart + j) * stride`（子核分担映射，沿用 03）。
- 合并对的 `block0→槽 j、block1→槽 j+1` 由 `dstStride=0` 保证；退化单 token 写槽 j，与基线逐行一致。
- **有效性计数**（有效行数统计变量）须同步：合并对 `+=2`，有效单 token `+=1`，与基线逐行计数结果一致。
- 慢路径（存在 `-1`/越界）下，合并要求两行均有效；任一无效即退化单 token，无效槽位保留累加器批首 `Duplicate(0)` 清零——合并**不破坏**清零契约。

### 5.3 游程增强（可选，仅长连续/等差段时）

```text
# 在配对前先吞掉极大均匀间隔游程
j = 0
while j < batchN:
    # 扫描 [j, k) 内 idx 升序且 gap 恒定
    k = j + 1
    while k < batchN and valid(k) and idx_k - idx_{k-1} == (idx_{j+1}-idx_j if j+1<batchN):
        k += 1
    runLen = k - j
    if runLen >= 2:
        g = idx_{j+1} - idx_j
        strideB = (g - 1) * rowLenB
        if 0 <= strideB < STRIDE_MAX and all valid in [j,k):
            DataCopyPad acc[j*rowLen], gm[(base+idx_j)*rowLen],
                        {blockCount=runLen, blockLen=rowLenB, srcStride=strideB, dstStride=0}
            j = k; continue
    # 否则单 token（或退回配对）
    ...
```

连续游程（`g=1`）⇒ `srcStride=0`，整段等价一段连续读，一条指令搬 `runLen` 个 token。

### 5.4 多段独立合并

- 不同源段（不同 GM、不同 `rowLen`）各自走配对循环，`rowLen`/`strideB` 各算；两段循环体可紧邻（同属一批 gather，共享同一批的 RAW 同步）。

---

## 6. 正确性红线

### 6.1 升序硬约束（正确性，非优化）

- 被合并行的源索引**必须升序** `idx_j < idx_{j+1}`（⇒ `gapRows>=1` ⇒ `srcStride>=0`）。
- 原因：目的槽位固定（`block0→槽 j`、`block1→槽 j+1`），`block0` 必须承载 `idx_j` 的数据。若 `idx_j > idx_{j+1}`（降序），`block0=idx_j` 源地址更高 ⇒ `srcStride` 为负 ⇒ 非法；若令起点为较小索引则会把数据写错槽（`idx_j` 的数据进了槽 `j+1`）。故**降序/相等对必须退化**为逐行（见陷阱 1）。
- 升序可由 `srcStride>=0` 隐式保证，但显式 `idx_j < idx_{j+1}` 判定更直观、防负 `gapRows`。

### 6.2 srcStride 单位与溢出

- `DataCopyPad` 的 `srcStride`/`dstStride` 是**相邻块间隔**（前块尾→后块头），非总跨步；总跨步 = `blockLen + stride`。
- **单位**：GM 源 → **字节**；`srcStrideB = (gapRows-1) * rowLen * sizeof(T)`。
- **溢出兜底**：`srcStrideB ∈ [0, STRIDE_MAX)`，`STRIDE_MAX` 取 `DataCopyExtParams.srcStride` 字段上限（如 `0x7FFFFFFF`/`INT32_MAX`）。实际行间隔产生的 stride 通常远小于此，仅作硬件上限兜底。

### 6.3 目的连续性与 03 契约

- 合并要求目的 `dstStride=0`（连续累加器）。若目的跨步（`dstStride≠0`）不可用，本策略不适用（先上 03）。
- **不破坏 03 的同步/清零契约**：合并仍受 03 批首 `MTE3_MTE2`(WAR)、批内 gather 后 `MTE2_MTE3`(RAW) 同步保护；慢路径无效槽位仍由 03 批首 `Duplicate(0)` 兜底，合并只覆写有效对的两槽。

### 6.4 有效性、边界与数值

- 合并要求**对内所有行有效**；含 `-1`/越界的对退化为逐行（逐行的 clamp(min=0)/skip 语义不变）。
- 合并的源起 `gm[(base+idx0)*rowLen]` 与逐行一致，`idx0 < srcRows` 保证不越界该 batch 的源行区。
- **不改变** gather 的值、有效性计数、scatter 目的位置、累加顺序、dtype。浮点结果与基线逐位一致（合并只改搬运编排，不改数值）。

---

## 7. 已知陷阱

### 陷阱 1：合并降序/相等索引（负/零 stride）

问题：未判升序就把相邻对合并，`idx_j >= idx_{j+1}` ⇒ `gapRows<=0` ⇒ `srcStride<0` 或目的槽错位。
症状：编译期 stride 非法，或运行时数据进错累加器槽位 → scatter 到 GM 后 KV 行错位，mismatch 集中在对应 token。
修复：严格 `idx_j < idx_{j+1}`（或 `srcStride>=0`）才合并；否则退化逐行（§6.1）。

### 陷阱 2：srcStride 单位/溢出误用

问题 A：把 `srcStride` 当"总跨步"或当元素数（应为字节）。
问题 B：无 `STRIDE_MAX` 兜底，极大行间隔使 stride 溢出字段。
症状：读错源地址（错位/越界）或编译/运行异常。
修复：`srcStrideB = (gapRows-1)*rowLen*sizeof(T)`（字节），并 `[0, STRIDE_MAX)` 兜底（§6.2）。

### 陷阱 3：目的非连续却假设 dstStride=0

问题：当前 gather 直写跨步 GM（无 05 累加器），强行 `blockCount=2, dstStride=0`。
症状：第二个 token 写入错误目的行，scatter 后 KV 错位。
修复：合并需连续目的；无累加器先上策略 03，再叠本策略（§4.1/§6.3）。

### 陷阱 4：合并含无效行的对

问题：对中一行为 `-1`/越界仍合并，按无效索引读 GM（垃圾）。
症状：无效 token 位置出现脏 KV。
修复：合并要求对内**两行均有效**；任一无效退化逐行（逐行按 clamp(0)/skip 处理，§6.4）。

### 陷阱 5：合并只省指令不省字节，误判 MTE2 不降为失效

问题：期望大幅降 `aiv_mte2_time`，实测降幅中等便以为无效。
诊断：合并**不改变搬运字节**，只降指令条数；`*_mte2_time` 是否降取决于 gather 是否**指令/延迟受限**（有效带宽远低于峰值 → 指令受限 → `*_mte2` 随指令数下降）。若 gather 已带宽饱和，`*_mte2` 几乎不动，收益仅在 `*_scalar`——仍属生效，非失效。

### 陷阱 6：误判整体未提速为策略失效

问题：本策略使 gather 读工作量下降，但整体 `Task Duration` 仅微降，误以为没生效而回退。
诊断：看 `aiv_mte2`/`aiv_scalar` 是否下降。下降而整体微动 = 瓶颈在 Cube 侧，本策略对 gather 已生效；整体提速需叠加 Cube 侧独立策略（见 §10）。

### 陷阱 7：有效性计数漏算

问题：合并对只 `+=1`（当成单条指令一行），漏算第二个 token。
症状：`valid_k`/有效行数统计偏小，下游（如 softmax mask/归一化）行为偏移。
修复：合并对有效行数 `+= 2`，有效单 token `+=1`，与逐行计数一致（§5.2）。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 搬运形态 | 哪个 gather 循环、每行是否 `blockCount=1`、源是否按运行时索引跳变、token 数 N |
| 源升序性 | 相邻 token 源索引是否升序（给出 sparse/topK 索引是否 `sort()` 的证据）；降序占比 |
| 目的连续性 | gather 是否写入连续累加器（`dstStride=0`）；若无，是否已上策略 03 |
| stride 推导 | `rowLen`、`srcStrideB=(gap-1)*rowLen*sizeof(T)` 公式、连续相邻 stride=0 验证 |
| 有效性 | 对内两行有效判定；`-1`/越界的 clamp/skip 与 03 清零契约是否保持 |
| stride 溢出 | `STRIDE_MAX` 取值与 `[0, STRIDE_MAX)` 兜底 |
| 合并粒度 | 用配对（blockCount=2）还是游程（blockCount=N）；游程需间隔均匀证据 |
| 多段 | 不同源段是否各自独立合并 |
| 瓶颈定位 | profiling `aiv_mte2`/`aiv_scalar` 占比与有效带宽；gather 是否关键路径、整体是否 Cube 受限 |
| 基线可重复 | 修改前 build/精度/性能基线值（须无 NPU 抢占） |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 同一轮混入 tiling 外层改动、累加器布局/深度调整、跨核同步改动、排序数据快路径、软流水或 Cube 侧改动。
- 改变 gather 值、有效性规则、scatter 目的位置、累加顺序、dtype。
- 合并降序/相等索引（陷阱 1）；漏 `STRIDE_MAX` 兜底（陷阱 2）。
- 目的非连续却 `dstStride=0` 合并（陷阱 3）；合并含无效行（陷阱 4）。
- 有效性计数漏算（陷阱 7）。
- 因某 shape 通过就跳过降序/相等对、全无效/部分无效、不同行长、跨段边界测试。

回退或缩小策略的条件：

- 索引恒降序、相邻对几乎不满足升序（合并率极低）→ 收益不及新增标量开销，回退或先升序化索引。
- 精度失败且无法定位到升序（陷阱 1）/stride（陷阱 2）/目的连续（陷阱 3）/有效性（陷阱 4）单一原因。
- profiling 显示 `aiv_mte2`/`aiv_scalar` **未下降**——说明 gather 非指令受限（已带宽饱和）或非该循环主导，重新归因（区别于陷阱 5/6 的"下降但整体微动"）。
- 依赖未验证的 `blockCount` 超限或 `srcStride` 超限才能合并；改用配对降级或缩小 run。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>
bash <build> --soc=<soc> --op=<op> --wheel
source <set_env>
pytest <op>/test/test_<op>_*.py        # 精度 + 性能（生成 profiling）
```

精度：与基线一致（沿用既有 `atol/rtol`）。合并只改搬运编排，浮点结果应与逐行**逐位一致**。

性能（**必须用 profiling 归因，不能只看整体 µs；且须无 NPU 抢占**）：

- gather 所在管线下时间明显下降；`*_scalar_time` 随指令数下降。
- 整体 `Task Duration` 不劣化；**整体提速是条件性的**——仅当该 gather 在关键路径上时才有显著整体下降。
- **本策略降的是 gather 读"指令数"，不是"搬运字节"**：
  - 若 gather **指令/延迟受限**（有效带宽 ≪ HBM 峰值）→ `*_mte2` 随指令数明显下降。
  - 若 gather 已**带宽饱和** → `*_mte2` 几乎不动，收益仅在 `*_scalar`（陷阱 5）。
- **整体持平若因 Cube 共瓶颈**（Cube 侧利用率已打满）→ 本策略对 gather 判定成功，整体提速需叠加 Cube 侧独立策略。**不可**把"整体微动"误判为本策略失效（陷阱 6）。

测量要点：

```text
- 重建后"首次"调用有冷启动假象（device kernel 缓存未热），稳态才真实；
  对比须在稳态、多次、无 NPU 抢占下做。共享 NPU 被他人占满时整体可劣化数倍，污染测量。
- 端到端 µs 受 chip/热/抢占影响波动较大；判据应以 profiling 的 aiv_mte2/aiv_scalar 降幅
  （机制层信号）为准，整体 µs 仅作旁证。
```

边界 shape：索引降序/相等对（退化）、`-1`/越界行（慢路径清零）、行长不同（多段）、不同 dtype（影响 `sizeof` 与对齐）、`batchN` 奇数（尾行单 token）、跨子核 stride 分担。

性能结论必须写清基线与归因：

```text
本策略收益相对"逐行 blockCount=1 gather"基线（通常已是策略 03 后的状态）；
判据是 gather 读管线 aiv_mte2/aic_mte2/aic_mte1 与 *_scalar 下降（指令数下降），
而非整体 µs。整体 µs 受 Cube 瓶颈限制时仅微动，须叠加 Cube 侧策略才得整体提速。
叠加 03 时，须相对"03 之后"的状态评估，避免基线错位。
```

## 检索卡（短卡）

动作：把逐行单块 DataCopyPad 改为以 blockCount+srcStride 一次搬运多个源块。
适用：索引 gather 逐行发 DataCopyPad，例如按 sparse/topK 索引读取 KV 行。
限制：被合并行的源索引必须严格升序：idx_j < idx_{j+1}。
范围：索引或 sparse/topK KV 行 gather 搬运循环。
检索词：indexed gather、sparse gather、DataCopyPad、blockCount、srcStride、升序索引。
机会：循环按运行时索引逐行发指令，且每行 blockCount=1。
