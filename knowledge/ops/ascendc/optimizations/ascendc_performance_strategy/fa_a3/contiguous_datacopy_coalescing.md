---
type: Optimization
title: 连续小搬运合并（per-element/per-row DataCopy → 单次批量 DataCopy）
description: 将循环内逐元素或逐行的小DataCopy合并为循环前一次批量预取，并只做一次等待。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/02-contiguous-datacopy-coalescing.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：连续小搬运合并（per-element/per-row DataCopy → 单次批量 DataCopy）

> **单一优化点：** 当一个循环对一段**连续**数据范围逐元素/逐行各发一条 `DataCopy`（每条仅搬 32B 对齐小块、且常伴随一条跨管线 `SetWaitFlag`）时，把 N 条小 `DataCopy` 合并为**一次覆盖整段的批量 `DataCopy`**，循环体改为对已预取到片上 buffer 的数据做 `GetValue`/`DataCopy(UB→UB)` 等廉价操作。降低搬运指令数、跨管线同步数与每条指令的固定开销。
>
> **算子/管线无关性：** 适用于 AscendC 任意管线（Vector 的 MTE2/MTE3、Cube 的 MTE2/MTE1）、任意方向（GM→UB、UB→GM、UB→UB、GM→L1、L1→L0）、任意算子，只要被合并的范围在源与目的都连续。不限于 FlashAttention。
>
> **两类典型合并点：** (a) 某阶段把连续索引/元数据的逐行 32B `DataCopy`(GM→UB) + 逐行 `SetWaitFlag<MTE2_S>` 合并为一次批量读；(b) 把连续多行输出的逐行 `DataCopy`(UB→GM) 合并为一次批量写。

本策略只合并"连续范围上的多条小 DataCopy"。不改变数学/数据语义、不改 tiling 结构、不改跨核同步、不引入软流水或新 buffer；被合并范围不连续时不在本策略范围（属 layout/tiling 重构）。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

低效基线在循环里逐元素/逐行搬运：

```text
# 模式 A：连续索引/元数据的逐行读（GM→UB）
for i in 0 .. N:
    DataCopy smallTile, gm[base + i], 32B_aligned   # 每次只取 1 个有用元素
    SetWaitFlag<MTE2_S>()                            # 每次一条跨管线同步
    v = buf.GetValue(intraOff)                       # PIPE_S 标量读

# 模式 B：连续输出行的逐行写（UB→GM）
for r in 0 .. dealRows:
    DataCopy gm[outRowOffset + r*rowStride], ub[r*rowLen], rowLen   # 每行一条 MTE3
```

每个小搬运带来：

- **搬运指令数 × N**：`DataCopy` 条数随 N 线性增长，每条有 issue/完成固定开销；payload 越小，固定开销占比越高（极端：32B 读只取 1 个 INT32，有效载荷 1/8）。
- **跨管线同步 × N**：若搬运跨越管线（如 MTE2→S、MTE2→V、V→MTE3），自动同步不覆盖，需逐条 `SetWaitFlag`，scalar 开销随 N 堆叠。
- **带宽利用率低**：多条小传输无法占满搬运带宽；同等总字节下，一条大传输更高效。

典型症状：profiling 显示该管线时间（`aiv_mte2`/`aiv_mte3`/`aic_mte2`/`aic_mte1`）或 `*_scalar_time` 占比高，且搬运次数多、单次 payload 小。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| DataCopy 批量搬运 | 一条 `DataCopy` 可覆盖任意 32B 对齐的连续范围，payload 从 32B 到整 buffer |
| 片上 buffer 随机读 | 数据进 UB/L1 后，`GetValue`(PIPE_S)/`DataCopy(UB→UB)`(V) 访问廉价，无需再触 GM、无需逐次同步 |
| 跨管线同步 | 合并后只需**一次** `SetWaitFlag` 守卫整段预取，下游 N 次消费共享这一次同步 |
| 计算流水 / 核间协作 | 沿用既有 TQue/flag，不改变流水与协议 |

核心改动：

```text
# 模式 A 改写：完整块批量预取 + 尾块 DataCopyPad，循环体改为 UB 内标量/复制
BLOCK = 32B / sizeof(T)
alignedStart = align_down(base, 32B)
needElems = intraOff + N                            # 调用方保证 base + N <= total
fullBlocks = floor(needElems / BLOCK); tailElems = needElems % BLOCK
DataCopy buf, gm[alignedStart], fullBlocks * BLOCK  # 1 条，32B 对齐段
if tailElems > 0:
    DataCopyPad(buf[fullBlocks * BLOCK], gm[alignedStart + fullBlocks * BLOCK], tailElems * sizeof(T))
SetWaitFlag<MTE2_S>()                              # 1 条，守卫全部下游 GetValue
for i in 0 .. N:
    v = buf.GetValue(intraOff + i)                 # 廉价 PIPE_S，无 GM、无逐次同步
    ... per-element 条件逻辑 ...

# 模式 B 改写：连续输出行单次批量写
DataCopy gm[outStartOffset], ub, dealRows * rowLen  # 1 条 MTE3（要求行间无 gap）
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 搬运形态 | 循环内逐元素/逐行 `DataCopy`，单条 payload 远小于一次能搬的连续范围 |
| 源连续性 | 被合并范围在**源**侧连续（或可由 `DataCopyParams`/`DataCopyPad` 的规则 stride 表达） |
| 目的连续性 | 被合并范围在**目的**侧连续（写回场景要求行 stride == 行长，无 inter-row gap/padding） |
| dtype 一致 | 整段同 dtype（批量 `DataCopy` 单 dtype） |
| 对齐 | 批量起始地址按 32B 对齐；完整块批量搬，尾部不足一块用 DataCopyPad 或逐元素回退；越界时夹紧 N 并同步缩短消费 |
| buffer 容量 | 批量范围 ≤ 目标片上 buffer（UB/L1）容量，且与并发占用不冲突 |
| 同步可合并 | 循环内的跨管线 `SetWaitFlag` 守卫的是同一批预取数据，可塌缩为一次 |

优先适用：

- N 较大（索引/元数据 gather、多行写回），profiling 显示对应管线或 scalar 占比高。
- 每条小搬运的**有效载荷占比低**（如 32B 读取 1 个 INT32）或**跨管线同步密集**。
- 循环体存在 per-element 条件逻辑，但**条件所依赖的连续元数据**可单独批量预取（见 §5.3）。

不适用或需先重构：

- 被访问范围**不连续**（按随机/非规则索引 gather 真正的数据，如按 `realIdx` 取 KV 行）——这属于 gather，不能直接合并；但若其**索引数组本身连续**，可合并索引预取（见 §5.3 区分）。
- 目的侧行间有 padding/gap（`rowStride > rowLen`），且无法用 `DataCopyPad` 表达——保留逐行或先改输出布局。
- 批量范围超 buffer 容量，且无法分块（需先 tiling，属另一策略）。
- 收益来自计算向量化、软流水、double buffer——非本策略。
- 循环内每条搬运依赖**前一条的运行时结果**（如读索引再决定下一步地址）——需先拆出"可批量预取的连续段"。

---

## 3. 合并范围与对齐规则

### 3.1 连续范围识别

- **读侧（gather 索引/元数据）**：`gm[base .. base+N)` 在 GM 中连续 → 可合并为 `[alignedStart, alignedStart+needElems)`（完整块 + 尾块）。
- **写侧（输出行）**：`gm[out0], gm[out0+rowStride], ...` 当 `rowStride == rowLen`（行间无 gap）→ 等价连续段 `[out0, out0 + dealRows*rowLen)`。

### 3.2 32B 对齐与越界保护（通用模板，INT32 例）

```text
BLOCK = 32B / sizeof(T)                 # INT32: 8
# 前置条件：idxStart + N <= totalElems。越界属于调用方错误：
# 必须夹紧 N 并同步缩短下游消费，不能只截断 readElems 后仍按原 N 消费。
alignedStart = floor(idxStart / BLOCK) * BLOCK
intraBase    = idxStart - alignedStart
needElems    = intraBase + N
fullBlocks   = floor(needElems / BLOCK)
tailElems    = needElems - fullBlocks * BLOCK

# 1) 完整块：批量 DataCopy（32B 对齐）
if fullBlocks > 0:
    DataCopy buf, gm[alignedStart], fullBlocks * BLOCK

# 2) 尾段：tailElems ∈ (0, BLOCK) 时用 DataCopyPad 精确搬 tailElems 个元素，
#    或逐元素回退；不得补读越过 totalElems，也不得把尾段丢弃。
if tailElems > 0:
    DataCopyPad buf[fullBlocks * BLOCK], gm[alignedStart + fullBlocks * BLOCK], tailElems * sizeof(T)
# 下游访问 buf[intraBase + i]，i in [0, N)
```

写侧批量写通常天然对齐（行长多为 32B 倍数），无需此 dance；但须确认 `dealRows*rowLen` 不越界目的分配。

### 3.3 同步塌缩

- 合并前：N 条 `SetWaitFlag<跨管线>`（每条守卫一次小搬运的下游消费）。
- 合并后：**1 条** `SetWaitFlag<跨管线>`，置于批量 `DataCopy` 之后、消费循环之前，守卫全部下游 `GetValue`/`DataCopy(UB→UB)`。
- 必须确认该同步事件类型与搬运→消费的管线对一致（如 GM→UB 是 MTE2，`GetValue` 是 S → 用 `MTE2_S`；UB→UB 计算是 V → 用相应事件）。误用事件类型（如把 S 当 V）是常见错误。

---

## 4. 数据与缓存布局

### 4.1 预取 buffer 选择

| 场景 | 推荐 buffer | 说明 |
|---|---|---|
| 连续索引/元数据预取（小，≤数 KB） | 复用既有标量/状态 buffer，时分复用 | 避免新增 buffer；确认与并发用途不冲突 |
| 连续数据行预取（较大） | 既有 VECIN/L1 工作块 | 走标准 TQue 双缓冲流水 |
| 输出批量写 | 既有 VECOUT/Fixpipe 输出 buffer | 直接批量 `DataCopy` 出 GM |

### 4.2 容量核算

```text
预取段字节 = ceil(needElems / BLOCK) * BLOCK * sizeof(T)   ≤ 预取 buffer 容量
写回段字节 = dealRows * rowLen * sizeof(T)   ≤ 目的 GM 分配（且 ≤ 输出 buffer）
```

完整块 + 尾块合计与 N 同量级；DataCopyPad 会把尾块补齐到 32B，预算按 `ceil(needElems/BLOCK)*BLOCK` 计。

---

## 5. 实施步骤

### 5.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| 循环所在 kernel 函数 | 循环前插入批量预取 `DataCopy` + 单次 `SetWaitFlag`；循环体把"小搬运"改为对预取 buffer 的 `GetValue`/`DataCopy(UB→UB)`；写回循环改为单次批量 `DataCopy` |
| Tiling / Host / 跨核同步 / 其他阶段 | **不改** |

### 5.2 模式 A：连续索引/元数据批量预取（读侧）

```text
# 基线
for i in stride分担 over N:
    DataCopy tmp, gm[align(idxOff)], BLOCK         # 每行 1 条 GM→UB
    SetWaitFlag<MTE2_S>()                          # 每行 1 条同步
    realIdx = tmp.GetValue(idxOff - aligned)

# 改写
idxUb = buf.Get<int32_t>()
if N > 0:
    (alignedStart, intraBase, needElems) = align32(base + offset, N, totalElems)  # §3.2
    # §3.2：完整块 DataCopy + 尾块 DataCopyPad；调用方保证 base+N <= totalElems
    fullBlocks = floor(needElems / BLOCK); tailElems = needElems % BLOCK
    DataCopy(idxUb, gm[alignedStart], fullBlocks * BLOCK)
    if tailElems > 0: DataCopyPad(idxUb[fullBlocks * BLOCK], gm[alignedStart + fullBlocks * BLOCK], tailElems * sizeof(int32_t))
    SetWaitFlag<HardEvent::MTE2_S>()               # 1 条，守卫全部 GetValue
for i in stride分担 over N:
    realIdx = idxUb.GetValue(intraBase + i)        # 廉价 PIPE_S，无 GM、无逐次同步
    ... per-element 条件分支（见 5.3）...
```

要点：

- `GetValue` 是 PIPE_S；MTE2 写 UB → S 读 UB 需 `MTE2_S` 同步，**只加一次**。
- `N==0` 必须短路（无预取、无同步、不进循环）。

### 5.3 关键区分：可合并的"连续元数据" vs 不可合并的"随机数据 gather"

循环体常含 per-element 条件（如 `realIdx<0 → 写零行；else → 按 realIdx gather KV 行`）。**只有连续的元数据（索引数组）可合并预取**；按 `realIdx` 取的数据行是随机/非连续的，**保持逐元素 gather**，但其循环体内不再触 GM 取索引（改读预取 UB）：

```text
for i ...:
    realIdx = idxUb.GetValue(intraBase + i)     # 连续索引：已批量预取
    if realIdx invalid:
        Duplicate zeroRow; DataCopy gm[zero]    # 零行写回（仍可单独评估是否合并）
    else:
        DataCopy rowIn, gm[kvBase + realIdx*rowLen], rowLen   # 随机 gather：保持逐行
        ... UB→UB 复制 → DataCopy gm[mergeBase + i*rowLen] ...
```

误把随机 gather 当连续合并是 §7 陷阱 1。

### 5.4 模式 B：连续输出行批量写回（写侧）

```text
# 基线
for r in 0 .. dealRows:
    DataCopy gm[(outBase + rowOffset + r) * rowLen], outHalf[r*rowLen], rowLen

# 改写（前提：行 stride == rowLen，行间无 gap）
outStart = (outBase + rowOffset) * rowLen
DataCopy gm[outStart], outHalf, dealRows * rowLen
```

要点：

- 仅当输出行在 GM 连续（`headDim==rowLen` 且 head 相邻无 padding）才可合并；否则用 `DataCopyPad` 或保留逐行。
- 批量写不改变 `aiv_mte3` 的**数据量**（字节相同），收益来自**指令数下降**（issue/scalar 开销），profiling 上 `aiv_mte3_time` 可能仅微降，`aiv_scalar_time` 下降更明显。

---

## 6. 正确性红线

### 6.1 对齐与越界

- 批量 `DataCopy` 起始/长度须 32B 对齐；不齐时按 §3.2 align-down-start / align-up-length。
- **越界保护与尾块**：读侧不能越过 GM 张量分配末尾；写侧不能越过目的分配。若请求范围越界，必须夹紧 N 并同步缩短下游消费，不能只截断读取长度；末尾不足一个块时用 DataCopyPad 或逐元素回退（§3.2）。
- `N==0`（空段）须短路，不得发起 0 长度/越界 `DataCopy`。

### 6.2 同步语义

- 合并后**单次** `SetWaitFlag` 必须覆盖**全部**下游消费（所有 `GetValue`/`DataCopy(UB→UB)` 都在该 Wait 之后）。
- 同步事件类型必须匹配搬运→消费的管线对（MTE2→S 用 `MTE2_S`，MTE2→V 用 `MTE2_V`，V→MTE3 用 `V_MTE3` 等）。**不得**误用（如把 S 当 V）。
- 走 TQue 的搬运（`EnQue/DeQue` 自动同步）不额外加 `SetWaitFlag`；只有手工 `DataCopy`+`GetValue` 这类同轮跨管线二次依赖才需要。

### 6.3 连续性契约

- 读侧：证明 `gm[base..base+N)` 连续（同张量、同 stride、无跳段）。
- 写侧：证明目的行 stride == rowLen（无 inter-row gap/padding）；若输出布局含 head 间隔或对齐 padding，**不可**直接合并。
- 多段连续（如多段子段拼接、多 head）须逐段证明；不连续则分段合并或保持逐行。

### 6.4 数值正确性

- 不改变读到的值、写出的值、条件分支语义、累加顺序、dtype。
- 预取的完整块 padding 与尾块补齐部分不得被下游使用；下游只访问 `[intraBase, intraBase+N)`。

---

## 7. 已知陷阱

### 陷阱 1：把随机 gather 当连续合并

问题：循环按运行时索引 `realIdx` 取数据行，误以为连续而合并。
症状：读错地址，mismatch 大面积。
修复：只有**索引/元数据数组**（其本身在 GM 连续）可合并预取；按 `realIdx` 取的数据行保持逐元素 gather（§5.3）。

### 陷阱 2：批量写越过行间 gap

问题：输出行间有 padding（`rowStride > rowLen`）却用单次连续 `DataCopy`，把 padding 位置当数据写或写越界。
症状：输出错位/踩踏相邻行。
修复：确认 `rowStride == rowLen`；不满足用 `DataCopyPad` 或逐行。

### 陷阱 3：同步漏加或事件类型错用

问题 A：合并后忘记加 `SetWaitFlag`，`GetValue` 读到未完成的 MTE2 写 → NaN/错值。
问题 B：事件类型用错（如 `MTE2_V` 守卫 `GetValue`，而 GetValue 是 S 不是 V）。
修复：合并后置单次正确事件类型的 `SetWaitFlag`（§6.2）。

### 陷阱 4：越界只截断读数、未缩短消费

问题：请求范围越过 totalElems 时只把读取长度向下截断，下游仍按原 N 消费，导致少读/读未初始化；或补读越过分配。
症状：运行时越界/数据错误。
修复：§3.2 夹紧 N 并同步缩短消费，尾块用 DataCopyPad/逐元素回退。

### 陷阱 5：N==0 未短路

问题：空段仍发起 `DataCopy`/`SetWaitFlag`，长度 0 或越界。
修复：`if (N > 0)` 守卫预取与同步。

### 陷阱 6：误判写侧收益

问题：期望批量写大幅降 `aiv_mte3_time`，实测几乎不变便回退。
诊断：写侧数据量不变，`aiv_mte3_time` 本就微变；收益在 `aiv_scalar_time`（指令数）。看 scalar 是否下降，别只看 mte3。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 搬运形态 | 哪个循环、哪个方向（GM↔UB/L1/L0）、单条 payload、循环次数 N |
| 源连续性 | 被合并范围在源是否连续（给出偏移/stride 证明） |
| 目的连续性（写侧） | 目的行 stride 是否 == rowLen（无 gap） |
| 对齐 | 32B 对齐处理（完整块 + 尾块 DataCopyPad）与越界夹紧 N 的方案 |
| buffer 容量 | 预取段 `ceil(needElems/BLOCK)*BLOCK*sizeof(T)` 是否 ≤ 选定 buffer |
| 同步 | 合并后单次 `SetWaitFlag` 的事件类型与守卫范围 |
| 条件逻辑 | 循环体是否有 per-element 条件；哪些是连续元数据（可合并）、哪些是随机数据（保持 gather） |
| 瓶颈定位 | profiling 对应管线/scalar 占比；确认是 op-count 受限而非带宽/算力受限 |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 同一轮混入 tiling 改动、buffer 深度调整、跨核同步改动、计算向量化、软流水。
- 改变读/写值、条件分支语义、累加顺序、dtype、输出布局。
- 把随机索引 gather 当连续合并（§7 陷阱 1）。
- 在行间有 gap 时强行批量写（§7 陷阱 2）。
- 漏加/错用同步事件（§7 陷阱 3）；越界只截断读数未缩短消费（§7 陷阱 4）；N==0 未短路（§7 陷阱 5）。
- 因某 shape 通过就跳过空段、尾块对齐越界、写侧多行/跨 head 边界测试。

回退或缩小策略的条件：

- buffer 容量超限且无法分块。
- 精度失败且无法定位到同步（§7 陷阱 3）/越界（§7 陷阱 4）/连续性（§7 陷阱 1/2）单一原因。
- profiling 显示对应管线时间**未下降**——说明该循环非瓶颈或搬运本就非 op-count 受限（如已是带宽受限），重新归因。
- 写侧收益判断须看 `aiv_scalar` 而非 `aiv_mte3`（§7 陷阱 6）。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>
bash <build> --soc=<soc> --op=<op> --wheel
source <set_env>
pytest <op>/test/test_<op>_*.py        # 精度 + 性能（生成 profiling）
```

精度：与基线一致（沿用既有 `atol/rtol`）。

性能（**用 profiling 归因**）：

- 读侧合并：对应 MTE2 时间显著下降，`*_scalar_time` 同步下降。
- 写侧合并：`*_scalar_time` 下降（指令数减少），对应 MTE3 时间**可能仅微变**（数据量不变，§7 陷阱 6）。
- 整体 `Task Duration` 不劣化；当被合并循环所在侧是关键路径时，整体明显下降。
- **与策略 01 的关系**：01（Cube K-tile 放大）可能使整体转为 Vector 受限；本策略（常落在 Vector 侧）正好攻击该瓶颈。两者叠加收益应相对"各自前序状态"评估，不能回到原始基线作增量起点。

边界 shape：`N==0`（空段）、`N<对齐块`（尾块 DataCopyPad/逐元素回退）、末尾越界夹紧 N、写侧 `dealRows` 多行/跨 head、不同 dtype（影响对齐块大小）。

性能结论必须写清基线与归因：

```text
本策略收益相对"逐元素小搬运"基线；判据是对应管线时间 + scalar 下降。
读侧看 MTE2/scalar 双降；写侧看 scalar 降（MTE3 可能微变，非失效）。
叠加 01 时，须相对"01 之后"的状态评估，避免基线错位。
```

## 检索卡（短卡）

动作：将循环内逐元素或逐行的小DataCopy合并为循环前一次批量预取，并只做一次等待。
适用：待搬数据构成32B对齐的连续范围。
限制：完整块批量 DataCopy 的起始地址和长度必须 32B 对齐；尾块用 DataCopyPad 精确长度或逐元素回退，不得越界或只截断读数。
范围：kernel循环中的连续GM到片上buffer搬运。
检索词：DataCopy批量搬运、连续范围、32B对齐、片上buffer、SetWaitFlag。
机会：循环内对连续数据逐元素或逐行发出小块DataCopy。
