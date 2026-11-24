---
type: Optimization
title: 索引 gather 相邻升序对合并读（blockCount=N + srcStride）+ UB 累加器批量 flush
description: 将逐块 gather 改为相邻升序对合并读取，并用 UB 累加器攒批后单条 flush。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/04-indexed-gather-merge-accumulator-batch.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：索引 gather 相邻升序对合并读（blockCount=N + srcStride）+ UB 累加器批量 flush

> **单一优化点：** 当一个 sparse / topK 索引 gather 循环**逐块**（每块若干行）把 GM 中按运行时索引跳变的源数据搬成连续 workspace——每块各发一条"GM→UB 读 + UB→workspace 写"两跳小 `DataCopyPad` 并夹密集跨管线同步——把它改成：**读侧**用 `DataCopyPad(blockCount=2, srcStride=源间隔)` 把源索引升序相邻的两块合并成一条指令读入 UB 累加器；**攒满 UB 行容量后**用一条 `DataCopyPad` 把整批一次性 flush 到 workspace（紧凑行宽）。把"N×2 笔碎 DMA + N×密集同步"塌缩为"≈N/2 笔合并读 + 极少笔批量 flush + 同比塌缩的同步"。本策略只改 gather 的搬运编排，不改任何计算语义、不改 tiling、不改 workspace 写入布局、不改跨核同步。
>
> **算子/管线无关性：** 适用于 AscendC 任意"按运行时索引逐块 gather 源数据 → 连续 workspace"的 Vector（MTE2/MTE3）或 Cube（MTE2/MTE1）管线。不限于任何具体算子；任何 sparse / topK / indirect gather + 中转 workspace 都可套用。前提：被合并对在**源侧升序相邻**（可由 `srcStride` 表达）、单块行数 ≤ UB 累加器行容量、UB 单缓冲跨批复用同步可正确编排。

---

## 1. 原理

该写法融合两个机制：**读侧相邻升序对合并**（用 `DataCopyPad` 的 `blockCount + srcStride` 把源侧跨步的两块合成一条读，压 gather 读指令数）+ **UB 累加器攒批 + 单条批量 flush**（把逐块中转写塌缩为攒满后一次性写出，压中转写指令数与跨管线同步数）。

本策略利用的硬件机制：

| 机制 | 利用方式 |
|---|---|
| `DataCopyPad` 跨步读（`blockCount + srcStride`） | 一条指令读 N 个源侧跨步块：`blockCount=2, blockLen=单块行字节, srcStride=源中两块间隔字节`。把相邻升序两块的 2 条读合成 1 条，**指令数 ÷2**（总字节不变） |
| 连续 UB 累加器（plain `TBuf`） | 即便源非连续，UB 内开一块连续 buffer 把 gather 结果紧凑排布（槽位 0..maxRows-1），攒满后一次性写出 |
| 单管线顺序 | 同一 MTE2 管线的多条 gather 读天然按序执行，无需逐条跨管线同步；只在 gather→flush 的跨管线边界加一次同步 |
| 单缓冲 WAR/RAW 复用 | 累加器单缓冲跨批复用：`MTE2_MTE3`（RAW：gather 写 UB 完 → flush 读 UB）+ `MTE3_MTE2`（WAR：flush 读 UB 完 → 下批 gather 覆写 UB），ping/pong 双 eventId 防 counter 累积 |
| 批量 flush | 攒满 UB 行容量后一条 `DataCopyPad` 把整批写到 workspace，**写指令数从 N 塌缩到 ceil(N×单块行数/累加器行容量)** |

定性 pipe 归因（相对）：`aiv_mte2`/`aiv_mte3`/`aiv_scalar` 三项同时大幅下降（碎 DMA 笔数 + 跨管线同步数同比塌缩）；`cube_utilization` 显著回升（vec gather 不再饿死 cube）。这是判断本策略是否对症的关键判据。

---

## 2. 性能问题模式（基线写法）

低效基线对每个被选中的 block 各发两跳 DMA（GM→UB→workspace），每跳夹一对跨管线同步：

```text
for blk in 0 .. validBlockCount:                       # validBlockCount 大（如 ~1k）
    idx = clamp(topkIndices[blk], oob -> 0)            # 运行时索引（gather，源非连续）
    ts  = idx * blockSize
    # 段A：GM→UB 读 blockSize 行
    DataCopyPad(acc, srcGm[srcBase + ts*rowElems], {blockCount=blockSize, srcStride=0})
    SetFlag<MTE2_MTE3>(); WaitFlag<MTE2_MTE3>()         # RAW：读完才许写
    # 段A：UB→ws 写 blockSize 行
    DataCopyPad(wsGm[wsBase + blk*blockSize*rowElems], acc, {blockCount=blockSize})
    SetFlag<MTE3_MTE2>(); WaitFlag<MTE3_MTE2>()         # WAR：写完才许下块复用 UB
    # 段B：partial/OOB 行 clamp 到 row(s2-1) duplicate（见 §3）
```

`blockSize` 小（如 1/2/4）下每个 block 仅几行（payload 小，常 ~1KiB 量级），开销源：
- **碎 DMA 笔数 × N×2**：每块一次 GM→UB + 一次 UB→ws，多路各一路 → 每内层步大量碎 DMA。payload 越小，每条指令的 issue/完成固定开销占比越高。
- **跨管线同步 × N×2**：每块两对 `MTE2_MTE3` + `MTE3_MTE2`，同步开销主导（scalar）。
- **带宽利用率低**：小传输无法占满 MTE2/MTE3 带宽；同等总字节下一条大传输远更高效。

典型症状：profiling 显示 `aiv_mte2`/`aiv_mte3`/`aiv_scalar` 三项同时高，且 `cube_utilization` 极低（cube 被 vec 的碎搬运阻塞、空等源数据落地）。

核心改动：
```text
BatchGather(srcGm, wsGm, ...):                          # 多路各调一次
  if blockSize > maxRows:  逐块退回                     # §4 退回条件
  ubRows = 0; wsBlkBase = blk
  while blk < validBlockCount:
      idx1 = clamp(indices[blk]); ts1 = idx1*blockSize
      if partial(ts1):  flush已攒批; 逐块退回; continue  # §3 段B clamp
      # 尝试两两 merge：blk 与 blk+1 升序相邻且 blk+1 非尾
      merge = (blk+1<N) && (ts2>ts1) && (ts2+blockSize<=s2)
      needRows = merge ? 2*blockSize : blockSize
      if ubRows+needRows > maxRows:  FlushAccumulator(); ubRows=0   # UB 满先 flush
      if merge:
          DataCopyPad(acc[ubRows], srcGm[srcBase+ts1*rowElems],
                       {blockCount=2, blockLen=blockSize*rowBytes, srcStride=(ts2-ts1-blockSize)*rowBytes})
          ubRows += 2*blockSize; blk += 2
      else:
          DataCopyPad(acc[ubRows], srcGm[srcBase+ts1*rowElems],
                       {blockCount=blockSize, blockLen=rowBytes, srcStride=0})
          ubRows += blockSize; blk += 1
  if ubRows>0:  FlushAccumulator()

FlushAccumulator():                                               # RAW → 批量写 → WAR
  SetFlag<MTE2_MTE3>(ping/pong); WaitFlag<MTE2_MTE3>()
  DataCopyPad(wsGm[wsBase+wsBlkBase*blockSize*rowElems], acc, {blockCount=ubRows, srcStride=0})
  SetFlag<MTE3_MTE2>(); WaitFlag<MTE3_MTE2>()
  toggle ping/pong
```

---

## 3. 正确性红线

### 3.1 OOB idx → 0（与参考实现的越界索引→0 契约一致）
- `idx < 0` 或 `idx >= maxBlock`（`maxBlock = CeilDiv(s2, blockSize)`）→ `idx = 0`。merge 对的 `idx1/idx2` 各自独立 clamp。

### 3.2 partial last block → clamp 到 row(s2-1)（段 A/段 B）
- 当 `tokenStart + blockSize > s2`（末块不足 blockSize 行），该块**必须退回**逐块路径：段 A 读 `validCount = s2 - tokenStart` 行，段 B 把剩余 OOB 行 duplicate `row(s2-1)`（clamp 到最后一行，匹配参考实现的 `clamp(max=S2-1)`）。
- **不得**把 partial 块塞进批量路径——批量路径不处理段 B clamp，OOB 行会读到脏数据。
- merge 对的第二块也要判 partial（`ts2 + blockSize <= s2`），否则不 merge、单块读（单块若 partial 会在下一轮被 §3.2 捕获退回）。

### 3.3 升序判定（srcStride 非负，关键易错）
- merge 必须满足 `ts2 > ts1`（即 `idx2 > idx1`）。整数 blockSize 下 `idx2 > idx1 ⟹ ts2-ts1 ≥ blockSize ⟹ srcStride = (ts2-ts1-blockSize)×rowBytes ≥ 0`。`idx2 == idx1`（重复索引）→ `ts2 == ts1` → 不 merge（单块读，正确）。**禁止**用 `ts2 >= ts1`（会把重复索引当 merge，srcStride 变负 → uint 下溢成巨大值）。

### 3.4 srcStride 单位（关键易错）
- `blockLen = blockSize × rowBytes`（字节），`srcStride = (ts2 - ts1 - blockSize) × rowBytes`（字节，**GM 操作数单位 = 字节**）。`dstStride=0`（UB 目的连续）。
- `DataCopyExtParams{blockCount=2, blockLen, srcStride, 0, 0}`。**勿**误用 32B-dataBlock 单位（那是 UB 操作数）。

### 3.5 写入语义不变（cube/ws/flag 零改动）
- workspace 落地数据逐位等价于逐块路径（同一 idx、同一 clamp、同一行宽）。cube 侧读 workspace 的偏移、跨核 flag 完全不变。

### 3.6 单缓冲 WAR/RAW 同步链（顺序固定）
- 每批严格：**MTE2（攒批写 UB）→ `MTE2_MTE3`(RAW) → MTE3（flush 读 UB 写 ws）→ `MTE3_MTE2`(WAR) → 下批 MTE2**。倒置/漏加任一条 → 单缓冲踩踏。
- `MTE2_MTE3` 用 ping/pong 双 eventId 交替（循环内反复 Set/Wait 同一 id 会 counter 失配）；`MTE3_MTE2` 单 id 即可（每次 Wait 紧跟 Set，不跨迭代累积）。
- flush 目的偏移 `wsBase + wsBlkBase×blockSize×rowElems` 必须与逐块路径的 `blk×blockSize×rowElems` 布局**逐位一致**，否则下游行错位。

### 3.7 已知陷阱
- **升序判定误用（srcStride 负值 underflow）**：用 `ts2 >= ts1` 而非 `ts2 > ts1`，遇重复索引时 `srcStride` 变负 → uint 下溢成巨大值 → 源地址飞到非法区、aiv aicore exception / 数据大面积错乱，常与存在重复索引的用例相关。修复：严格 `ts2 > ts1`。
- **srcStride 单位/换算错**：漏乘 `rowBytes`（传行数而非字节），或误用 32B-dataBlock 单位 → 合并对读到错误源行，行错位；或越界读 GM。修复：GM 操作数 `srcStride` 单位 = 字节。
- **partial 末块漏退回（段 B clamp 丢失）**：忘记判 `partial1 = (ts1+blockSize > s2)` → OOB 行读到越界脏数据而非 clamp 的最后一行。症状：仅当 `s2 % blockSize != 0` 的用例 mismatch；`blockSize=1` 用例（无 partial）不触发，易漏测。修复：每轮先判 partial。
- **UB 容量溢出（攒批超 maxRows）**：`ubRows + needRows > maxRows` 检查漏掉或阈值错 → 攒批越界写 UB 尾部，踩踏相邻 buffer。修复：每次读前检查；`needRows = merge ? 2*blockSize : blockSize`。
- **同步链倒置/漏加（单缓冲踩踏）**：Flush 漏 RAW 或 WAR，或顺序错 → MTE3 读到未完成/被覆写的 gather 数据 → NaN/错值，偶发难复现。修复：每批严格 RAW→flush→WAR。
- **blockSize > UB 行容量未退回**：大块仍走批量路径，`blockCount=blockSize > maxRows` 越界写 UB → 编译期或运行期 UB 越界。修复：函数入口 `if (blockSize > maxRows) { 逐块退回; return; }`。
- **wsBlkBase 目的偏移错位**：`wsBlkBase` 跟踪错（partial 退回后未更新为 `blk+1`，或 flush 后未重置为当前 blk）→ flush 写到错误行号，下游行错位（gather 数据本身正确）。修复：每次 flush 后置为当前 `blk`；partial 退回后置 `blk+1`。

---

## 4. 泛化条件

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| gather 形态 | 逐块按运行时索引 gather 源行 → 连续 workspace，每块两跳 DMA + 跨管线同步（§2 模式） |
| 单块装得下 UB | `blockSize ≤ UB 累加器行容量`。`blockSize` 过大 → 整块装不下，**必须退回**逐块 |
| 源索引升序相邻（仅 merge 对） | 相邻两块满足 `ts2 > ts1`（⇒ `srcStride ≥ 0`）且 `ts2+blockSize ≤ s2`（第二块非 partial）。降序/相等/重叠/第二块 partial → 不 merge，单块读 |
| UB 容量 | 累加器 `maxRows × rowElems × sizeof(T)` ≤ 可用 UB（须与并发占用核算）；攒批 + 2×blockSize 不溢出 |
| 目的布局可由 flush 表达 | workspace 写入紧凑行宽（行间无 gap），单条 `DataCopyPad(blockCount=ubRows, srcStride=0)` 可表达 |
| 同步可塌缩 | gather 内部同 MTE2 管线无需跨管线同步；只在 gather→flush 边界加 RAW/WAR |
| 基线稳定 | 修改前 build/精度/perf 可重复 |

优先适用：
- `blockSize` 小（1/2/4），validBlockCount 大，碎 DMA + 密集同步主导。
- profiling 显示 `aiv_mte2`/`aiv_mte3`/`aiv_scalar` 三高且 `cube_utilization` 低（vec gather 饿死 cube）。
- 源索引在结果中常呈升序/局部升序（如某类 topK 的索引往往聚集相邻 token）。

不适用或需先重构：
- `blockSize > UB 累加器行容量` 且无法扩容 → 退回逐块（本策略的退回路径，非失败）。
- 源与目的**都连续** → 直接用连续搬运合并（无需 UB 暂存）。
- 目的行间有 padding/gap（`rowStride > rowLen`）且无法用 `DataCopyPad` 表达 → 保留逐行或先重构布局。
- 收益来自计算向量化、软流水、double buffer → 非本策略。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| **gather 所在 kernel 函数** | 把逐块 `for(blk)` 循环（多路各调逐块函数）替换为多次 `BatchGather`（每路一次）；新增 `BatchGather`（攒批 + 两两 merge + 退回）与 `FlushAccumulator`（批量 flush + 同步链） |
| InitBuffers | 复用既有 UB 累加器（plain `TBuf`，`maxRows×rowElems`），**不新增 buffer**；复用既有 ping/pong eventId |
| Tiling / Host / 跨核同步 / cube 消费侧 | **不改**（workspace 写入布局不变，cube/ws/flag 零改动） |

### 5.2 数据与缓存布局
- **UB 累加器**：复用既有 plain `TBuf`（非 TQue），`maxRows × rowElems` 元素。槽位 j ∈ [0, ubRows) 存第 j 行，相邻行无 gap。单缓冲跨批复用（靠 §3.6 的 WAR/RAW）。不用 TQue，以手工控制跨管线同步（TQue 自动同步会强制插中间 hop，正是要消除的开销源）。
- **攒批行计数**：`ubRows` 按"实际读入的物理行数"累加（merge 对 +2×blockSize，单块 +blockSize）；上限 `maxRows`。放不下先 flush 再续读。
- **workspace 写入布局**：`wsGm[wsBase + blk×blockSize×rowElems]`，紧凑行宽，**与逐块路径完全一致**。批量 flush 的 `blockCount=ubRows, srcStride=0` 写出 ubRows 个连续行，落在 `wsBlkBase` 起始的连续区——因 gather 按 blk 顺序攒批，目的行号连续，srcStride=0 正确。
- **源侧跨步**：merge 对的 `srcStride = (ts2-ts1-blockSize)×rowBytes`（字节）。

---

## 6. LLM 前置问题

| 问题 | 必填内容 |
|---|---|
| gather 形态 | 哪个循环、各路几路、validBlockCount、blockSize、每块几跳 DMA + 几条同步 |
| UB 累加器 | 复用哪个 `TBuf`、行容量 `maxRows`、单块 `blockSize` 是否 ≤ maxRows |
| 升序/相邻 | 源索引是否常升序相邻？merge 判定条件（`ts2>ts1` 且 `ts2+blockSize≤s2`） |
| srcStride | 推导：`(ts2-ts1-blockSize)×rowElems×sizeof(T)`，单位字节（GM） |
| 退回条件 | blockSize>maxRows 退回？partial 末块（`ts1+blockSize>s2`）退回？退回路径是否保留段 B clamp |
| 同步 | Flush 的 RAW(`MTE2_MTE3`)/WAR(`MTE3_MTE2`) 落点；ping/pong eventId |
| 目的布局 | workspace 写入是否紧凑行宽（无 gap）；flush `blockCount=ubRows, srcStride=0` 是否匹配 |
| OOB 语义 | idx 越界 → 0；partial OOB 行 → clamp 到最后一行；是否与参考实现一致 |
| 瓶颈定位 | profiling `aiv_mte2`/`aiv_mte3`/`aiv_scalar`/`cube_utilization` 基线值 |
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

精度：与基线一致（本策略精度中性，只改搬运不改计算）。不得出现任何新 FAIL。

性能（**用 profiling 归因**，相对）：
- `aiv_mte2_time` / `aiv_mte3_time` 大幅下降（碎 DMA 笔数塌缩 + 同步数塌缩）。
- `aiv_scalar_time` 下降（跨管线同步数大幅塌缩）。
- `cube_utilization` 显著回升（vec gather 不再饿死 cube）——这是本策略的标志性判据。
- **判据**：`aiv_mte2`/`aiv_mte3`/`aiv_scalar` 三降 + `cube_utilization` 回升。若三者未降，说明该 gather 非瓶颈或非碎 DMA + 密集同步主导（可能已是带宽受限），重新归因；若 `cube_utilization` 未回升，说明 cube 瓶颈另有它因。

边界 shape（必测）：
- `blockSize=1`（mergePossible 恒真、无 partial）。
- `blockSize>1 且 ≤ maxRows/2`（merge 对 + 单块混合）。
- `blockSize` 落在 `[maxRows/2+1, maxRows]`（批量路径但不 merge，`2×blockSize > maxRows`）。
- `blockSize > maxRows`（退回逐块，验证不崩、精度不变）。
- `s2 % blockSize != 0`（partial 末块，验证段 B clamp 退回）。
- 降序/重复 topK 索引（验证不 merge、单块读）。
- 不同行宽（影响 rowBytes / 32B 对齐）、不同 dtype。

回退或缩小策略的条件：
- UB 累加器超容量且无法退回/缩批。
- 精度失败且无法定位到 srcStride（陷阱 2）、partial（陷阱 3）、同步（陷阱 5）、偏移（陷阱 7）单一原因。
- profiling 显示 `aiv_mte2`/`aiv_mte3`/`aiv_scalar` **未下降**（重新归因）；`cube_utilization` 未显著回升。

与其它策略的关系：与同族策略 05（scatter 侧批量化）**对称**——本策略是 gather 侧（读源进 workspace），策略 05 是 scatter 侧（写源出 workspace）。两者机制同构（攒批 + 单条批量搬 + 单缓冲 WAR/RAW），方向相反，可叠加。独立于 workspace 单份化（01）、收尾并行（02）、bf16 matmul（03）——本策略只改 gather 搬运编排，互不冲突，可叠加。

## 检索卡（短卡）

动作：将逐块 gather 改为相邻升序对合并读取，并用 UB 累加器攒批后单条 flush。
适用：按运行时索引逐块 gather 源行到连续 workspace，且每块有两跳 DMA 与同步。
限制：须保持越界索引→0契约。
范围：稀疏或 topK 索引 gather kernel
检索词：indexed gather、DataCopyPad、blockCount、srcStride、UB 累加器、批量 flush
机会：每个选中 block 都单独发 GM→UB→workspace 两跳 DMA，并夹跨管线同步。
