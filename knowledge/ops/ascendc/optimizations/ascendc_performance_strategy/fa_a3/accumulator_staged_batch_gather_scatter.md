---
type: Optimization
title: 累加器暂存的批量 gather / 批量跨步 scatter
description: 将逐行中转改为批循环，在连续UB累加器中紧凑gather，再批量scatter。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/03-accumulator-staged-batch-gather-scatter.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：累加器暂存的批量 gather / 批量跨步 scatter

> **单一优化点：** 当一个循环对**非连续（按索引 gather）**的源行做 `GM→UB→…→GM` 逐行中转、且每行伴随跨管线下同步时，改为：用一个**连续的批量累加器 buffer** 逐行 `GM→UB` 累积（全部在同一搬运管线、无逐行跨管线同步），再用**单条带 `blockCount + dstStride` 的 `DataCopyPad`** 把整批一次性跨步 scatter 到 GM。把"N 次逐行中转 + N×跨管线同步"塌缩为"一批同管线 gather + 一次 RAW 同步 + 一次批量 scatter"。
>
> **算子/管线无关性：** 适用于 AscendC 任意管线的 gather/scatter 循环（Vector MTE2/MTE3、Cube MTE2/MTE1），源/目的只要可按"逐行 GM→UB 累积 + 单条跨步搬出"建模即可。不限于 FlashAttention。
>
> **与策略 02 的区别：** 02 要求源与目的**都连续**，把 N 条小 copy 合并成 1 条（数据本身已连续，无需暂存）。本策略处理**源非连续（gather）、目的可能跨步**的场景——gather 仍是 N 次小读，但通过连续累加器把"逐行跨管线中转"塌缩为"同管线批量 + 单条 scatter"，并消除中间管线 hop。两者互补：连续用 02，gather/跨步用 03。
>
> **与策略 04（删纯桥 hop）的区别：** 04 只删"无变换的中转管线段"，与是否批量无关；本策略的核心收益来自批量化。两者正交，可叠加。

本策略只把"逐行 gather/scatter 中转"改成"累加器批量 + 单条跨步 scatter"。不改变数据语义/数值、不改 tiling 外层结构、不改跨核同步、不引入软流水或新管线。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

低效基线逐行做 GM→UB→GM 中转（典型如按稀疏/索引 gather KV 行再写到连续 workspace）：

```text
for i in gather rows:                          # 源按 realIdx 非连续
    DataCopy ub_in,  gm[srcIdx*rowLen], rowLen          # GM→UB (MTE2)
    <跨管线同步 MTE2→下游>                                # 每行 1 条
    DataCopy ub_out, ub_in, rowLen                        # UB→UB (V 复制，桥)
    <跨管线同步 V→MTE3>                                   # 每行 1 条
    DataCopy gm[dstRow*i*rowLen], ub_out, rowLen          # UB→GM (MTE3)
```

每个 gather 行带来：

- **搬运指令数 × N**：每行多段 DataCopy（读 + 桥复制 + 写），issue 开销随 N 线性堆叠。
- **跨管线下同步 × N**：每行至少 1~2 条 `SetWaitFlag`（MTE2→V、V→MTE3 等），scalar 开销主导。
- **中间管线 hop**：为满足 TQue 同步语义常引入 UB→UB 的 V 复制桥，多一个 hop 与一次同步。

典型症状：profiling 显示 `aiv_scalar`/`aiv_mte2`/`aiv_mte3`（或 cube 对应管线）占比高，且循环次数大、单行 payload 相对小。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 连续 UB 累加器 | 即便源/目的非连续，UB 内可开一块**连续**的批量大小区 buffer，把 gather 结果紧凑排布 |
| 单管线顺序 | 同一管线的多次 `DataCopy` 天然按序执行，无需逐次跨管线同步；只在**跨管线边界**加一次同步 |
| `DataCopyPad` 跨步搬运 | `blockCount + srcStride/dstStride` 一条指令写 N 个跨步目的行（GM 目的 dstStride 单位=字节） |
| 单缓冲复用同步 | 累加器单缓冲跨批复用时，用 WAR（搬出→gather）+ RAW（gather→搬出）两条手工同步保证不踩踏 |

核心改动：

```text
BATCH = 选定批大小（行）
for chunkStart in rows step BATCH:
    batchN = min(BATCH, rows - chunkStart)
    SetWaitFlag<MTE3_MTE2>()                         # WAR：上一批搬出完，才许本批 gather 覆写
    for j in 0 .. batchN:                            # 全在 MTE2 单管线，无逐行跨管线同步
        DataCopyPad acc[j*rowLen], gm[srcIdx_j*rowLen], {blockLen=rowLenB, stride=0}
    SetWaitFlag<MTE2_MTE3>()                         # RAW：本批 gather 完，才许搬出
    DataCopyPad gm[dstFirst*rowLen], acc,            # 1 条：blockCount=batchN, dstStride=跨步
                {blockCount=batchN, blockLen=rowLenB, srcStride=0, dstStride=(stride-1)*rowLenB}
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 循环形态 | 逐行/逐元素 `GM→UB→GM`（或 `GM→UB→…→GM`）中转，源按索引非连续 gather |
| 可批化 | 连续若干 gather 行可攒进一块 UB（顺序无关，只要能排进累加器槽位 0..BATCH-1） |
| 目的可跨步表达 | 目的行的间距恒定（跨步 S），可用 `DataCopyPad` 的 `dstStride` 表达；或目的连续（S=1） |
| UB 容量 | BATCH 行 × 行长 × sizeof(T) ≤ 可用 UB（须与并发占用核算） |
| 对齐 | 每行 blockLen 建议 32B 对齐（不齐时 `DataCopyPad` 支持，但需处理 dummy/越界） |
| 同步可塌缩 | gather 内部无需跨管线同步（同管线），只在 gather→scatter 边界同步 |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- gather 行数大、每行中转带跨管线同步（`aiv_scalar`/`aiv_mte2`/`aiv_mte3` 主导）。
- 原实现存在 UB→UB 的 V 复制桥（TQue 同步语义驱动），可由"累加器 + 手工同步"替代。
- 目的跨步恒定（如子核 stride-2 分担、或固定 head 间隔）。

不适用或需先重构：

- 源**连续**且目的**连续** → 直接用策略 02（无需暂存）。
- 目的跨步不恒定（每行间距不同）→ 无法用单条 `dstStride` 表达，保留逐行或先重构布局。
- BATCH 行超 UB 且无法缩小批（需先 tiling）。
- 收益来自计算向量化、软流水、double buffer——非本策略。
- gather 行间存在**真数据依赖**（前一行结果决定后一行地址）→ 需先拆出可批化的独立段。

---

## 3. 批大小与累加器选择

```text
BATCH 选择：在 UB 容量内尽量大（减少同步次数），但受限于：
  - 累加器字节 = BATCH * rowLen * sizeof(T)  ≤ 可用 UB 余量
  - BATCH 宜为子核分担 stride 或行分块的公约数，避免尾块碎片
  - 同步次数 = 2 * ceil(rows / BATCH)（WAR+RAW 各一/批）；BATCH 越大越少
```

同一数据通路中若存在多段（如按字段/分块拆分的多个段）需各自 gather/scatter，可各开独立累加器，同批并行 gather/scatter。

---

## 4. 数据与缓存布局

### 4.1 累加器布局

- 累加器为**连续** plain `TBuf`（非 TQue）：槽位 j ∈ [0, BATCH) 存第 j 行，偏移 `j * rowLen`，相邻行无 gap。
- 单缓冲即可（靠 §6 的 WAR/RAW 同步跨批复用）；如需 gather 与 scatter 重叠可升级双缓冲（非本策略）。
- 不用 TQue 是为了**手工控制跨管线同步**（TQue 的 EnQue/DeQue 自动同步会强制插入中间 hop，正是要消除的 V 桥根源）。

### 4.2 目的跨步布局

- 目的第 j 行落在 `gm[dstFirst*rowLen + j * S * rowLen]`，S 为跨步（如子核 stride-2 ⇒ S=2）。
- 单条 `DataCopyPad`：`blockCount=batchN`、`blockLen=rowLen*sizeof(T)`、`srcStride=0`（UB 连续）、`dstStride=(S-1)*rowLen*sizeof(T)`（GM，字节单位，见 §6.3）。

---

## 5. 实施步骤

### 5.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| gather/scatter 所在 kernel 函数 | 把逐行中转循环改为"批循环 + 累加器 gather + 单条跨步 scatter"；新增累加器 `TBuf` |
| InitBuffers | 新增累加器 `TBuf`；必要时从过大的既有 buffer 收紧容量腾空间（见 §5.4） |
| Tiling / Host / 跨核同步 / 其他阶段 | **不改** |

### 5.2 批量 gather + 批量 scatter 主循环

```text
acc = accBuf.Get<T>()                            # 连续累加器
for chunkStart in rows step BATCH:
    batchN = min(BATCH, rows - chunkStart)

    # (1) WAR：单缓冲复用——等上一批 scatter(MTE3 读) 完，才许本批 gather(MTE2 写) 覆写
    SetWaitFlag<MTE3_MTE2>()

    # (2) 批量 GM→UB 累积（同 MTE2 管线，无逐行跨管线同步）
    for j in 0 .. batchN:
        srcIdx_j = <按本行索引/gather 语义>      # 可含有效/无效判定（见 §6.4）
        DataCopyPad acc[j*rowLen], gm[srcIdx_j*rowLen],
                    {blockCount=1, blockLen=rowLenB, srcStride=0, dstStride=0}

    # (3) RAW：本批 gather(MTE2 写) 完，才许 scatter(MTE3 读)
    SetWaitFlag<MTE2_MTE3>()

    # (4) 单条跨步 UB→GM
    dstFirst = <本批首行的全局目的行号>
    DataCopyPad gm[dstBase + dstFirst*rowLen], acc,
                {blockCount=batchN, blockLen=rowLenB, srcStride=0,
                 dstStride=(S-1)*rowLenB}         # S=目的跨步
```

### 5.3 消除中间管线 hop（V 桥）

- 原逐行设计常因 TQue 同步语义引入 `UB→UB` 的 V 复制桥（如 VECIN TQue 自动插 MTE2→V，再经 VECOUT 插 V→MTE3）。
- 改用 plain `TBuf` 累加器 + 手工 `MTE3_MTE2`/`MTE2_MTE3` 同步后，路径变为 `GM→(MTE2)→累加器→(MTE3)→GM`，**V 复制整段删除**，少一个 hop 与一类同步。
- 这是 scalar 管线开销下降的主因之一（跨管线同步数大幅塌缩）。

### 5.4 UB 容量重打包（按需）

- 新增累加器若超 UB，先审查既有 buffer 是否过量分配（如 Cast/输出 buffer tileSize 实际有上界），收紧后腾空间。
- 例如：某输出/中转 buffer 若实际单次写入量存在小于其分配量的上界，可按该上界收紧容量，把差额腾给累加器。
- 重打包后须重算 UB 合计 ≤ 硬件上限（如 Ascend 910B 系列 UB 192KB，以 ascend-hardware 实际规格为准），并确认时分复用不冲突。

---

## 6. 正确性红线

### 6.1 单缓冲 WAR/RAW 同步顺序

- 跨批复用同一累加器（单缓冲）时，**必须**：
  - 批首 `SetWaitFlag<MTE3_MTE2>`（WAR：上一批 scatter 读完，本批 gather 才许写）；
  - gather 后 `SetWaitFlag<MTE2_MTE3>`（RAW：本批 gather 写完，scatter 才许读）。
- 首批无"上一批"，但**仍需**保证 scatter 不读到未初始化数据——要么首批前有等价的初始同步，要么首批 gather 先于任何 scatter（自然成立）。
- 顺序倒置或漏加 ⇒ 单缓冲踩踏/读未完成数据 ⇒ NaN/错值（见 §7 陷阱 1）。
- 升级双缓冲可去掉 WAR（两槽交替），但非本策略。

### 6.2 累加器槽位与无效/尾块

- **尾批** `batchN < BATCH`：scatter 的 `blockCount=batchN`（不是 BATCH），只搬有效行。
- **无效/未用槽位**（gather 跳过的行）：单缓冲复用下槽位残留上批或未写数据，**必须**处理：
  - 或在批首 `Duplicate` 清零整批槽位（慢路径）；
  - 或保证未用槽位的旧值不会被下游当作有效行（下游按 `valid_count`/mask 截断）。
  - 不能假设未用槽位为 0（除非显式清零）。
- 批首是否清零取决于"是否存在未用槽位 + 下游是否容忍"；通用安全做法是慢路径清零。

### 6.3 dstStride 语义（关键，易错）

`DataCopyPad`/`DataCopyExtParams` 的 `srcStride`/`dstStride` 是**相邻数据块间的间隔**（前一块尾 → 后一块头），**不是**总跨步：

- 单位：操作数在 **GM** → **字节**；操作数在 **VECIN/VECOUT(UB)** → **dataBlock(32B)**。
- 总跨步（块起点→下一块起点）= `blockLen + stride`（各自单位）。
- 跨步 S（目的每隔 S 行写一行，行长 = blockLen）：
  - GM 目的：`dstStride = (S - 1) * rowLenBytes`（字节）。S=2 ⇒ `dstStride = rowLenBytes = blockLen`。
  - UB 目的：`dstStride = (S*rowLenBytes - rowLenBytes)/32`（dataBlock 数）。
- 源累加器连续 ⇒ `srcStride = 0`。

示例（跨步 S=2、GM 目的）：设行长 `rowLenBytes = blockLen`，则 `dstStride = rowLenBytes`，总跨步 `blockLen + dstStride = 2 × rowLenBytes`，即每隔 2 行写一行。

### 6.4 对齐与越界

- 每行 `blockLen` 建议 32B 对齐；不齐时 `DataCopyPad` 支持，但末尾 dummy/对齐填充须不影响有效数据（搬出到 GM 时框架自动丢弃 dummy）。
- GM 起始/长度不得越界目的分配；尾批按 `batchN` 收口。
- 累加器容量 `BATCH*rowLen*sizeof(T)` 不得超 `TBuf` 分配。

### 6.5 数值正确性

- 不改变 gather 的值、scatter 的目的位置、有效行计数语义、dtype。
- gather 索引的有效/无效判定与下游（如 softmax mask）语义须一致；本策略不改变有效性规则，只改变搬运编排。

---

## 7. 已知陷阱

### 陷阱 1：单缓冲 WAR/RAW 同步倒置或漏加

问题：单缓冲累加器跨批复用，漏 `MTE3_MTE2`（WAR）或 `MTE2_MTE3`（RAW），或顺序错。
症状：MTE3 读到未完成/被覆写的 gather 数据，或 MTE2 覆写未搬出的上批 ⇒ NaN/错值，常表现为偶发或与批数相关。
修复：每批严格 `MTE3_MTE2`(首) → gather → `MTE2_MTE3`(gather 后) → scatter（§6.1）。

### 陷阱 2：dstStride 单位/语义误用

问题：把 `dstStride` 当"总跨步"而非"间隔"，或混淆 GM(字节) 与 UB(32B block) 单位。
症状：scatter 行错位、写越界、踩踏相邻行。
修复：按 §6.3——`dstStride` 是间隔，总跨步 = `blockLen + dstStride`；GM 用字节，UB 用 32B block。

### 陷阱 3：尾批 blockCount 未收口

问题：scatter 用 `blockCount = BATCH` 而非 `batchN`，尾批多搬未写槽位（残留上批/垃圾）到 GM。
症状：尾块目的行写错。
修复：`blockCount = batchN`（§6.2）。

### 陷阱 4：未用槽位残留未清零

问题：gather 跳过无效行，对应累加器槽位残留旧值，scatter 把旧值当有效写出。
症状：无效/缺行位置出现脏数据。
修复：批首 `Duplicate` 清零（慢路径），或下游按 valid_count/mask 截断（§6.2）。

### 陷阱 5：累加器超 UB / 时分复用冲突

问题：新增累加器使 UB 合计超过硬件上限，或与并发阶段（如多个 vec 子核/阶段的时分复用）冲突。
症状：编译期 buffer 校验失败或运行踩踏。
修复：§5.4 重打包既有 buffer 腾空间；重算 UB 合计并确认串行时分复用无冲突。

### 陷阱 6：误把连续场景用本策略

问题：源与目的都连续却开累加器暂存，徒增一次 GM→UB 与同步。
修复：连续场景用策略 02（直接合并），本策略仅用于 gather/跨步（§2）。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 循环形态 | 哪个 gather/scatter 循环、每行几段 DataCopy、几条跨管线同步、行数 N |
| 源非连续性 | 源是否按索引 gather（非连续）；连续则改用 02 |
| 目的跨步 | 目的行间距是否恒定 S；`dstStride` 推导（GM 字节 / UB 32B block） |
| 批大小 | BATCH 取值与累加器字节核算（≤ UB 余量） |
| 同步 | WAR(`MTE3_MTE2`)/RAW(`MTE2_MTE3`) 的落点与单缓冲复用正确性 |
| 无效/尾块 | 未用槽位清零策略、尾批 `blockCount=batchN` |
| UB 容量 | 是否需重打包既有 buffer；合计 ≤ 硬件上限 |
| 瓶颈定位 | profiling 对应管线/scalar 占比；确认是逐行中转+跨管线同步主导 |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 同一轮混入 tiling 外层改动、跨核同步改动、计算向量化、软流水、double buffer、或排序数据快路径（那是独立优化）。
- 改变 gather 值、scatter 目的位置、有效性规则、dtype。
- 单缓冲漏加/倒置 WAR/RAW（陷阱 1）。
- 误用 `dstStride` 单位或当总跨步（陷阱 2）。
- 尾批不收口 `blockCount`（陷阱 3）；未用槽位不清零（陷阱 4）。
- 连续场景用本策略（陷阱 6）。
- 因某 shape 通过就跳过尾批、全无效/部分无效、跨步非 2、不同 dtype 测试。

回退或缩小策略的条件：

- 累加器超 UB 且无法重打包/缩批。
- 精度失败且无法定位到 WAR/RAW（陷阱 1）、stride（陷阱 2）、尾块/清零（陷阱 3/4）单一原因。
- profiling 显示对应管线/scalar **未下降**——说明该循环非瓶颈或非逐行中转主导，重新归因。
- 目的跨步不恒定，无法用单条 `dstStride` 表达。

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

- 对应搬运管线时间（如 `aiv_mte2`/`aiv_mte3`）显著下降。
- `aiv_scalar_time`/`aic_scalar_time` 显著下降（跨管线同步数塌缩）。
- 整体 `Task Duration` 不劣化；当该循环所在侧是关键路径时整体明显下降。
- **与 01/02 的关系**：01（Cube K-tile）可能使整体转为 Vector 受限；02（连续合并）处理连续段；本策略处理 gather/跨步段。三者收益应相对"各自前序状态"评估，不能回到原始基线作增量起点。

边界 shape：`rows < BATCH`（单批尾）、`rows % BATCH != 0`（尾批）、全无效/部分无效行（槽位清零）、跨步 S≠2、不同 dtype（影响对齐与 stride 字节换算）。

性能结论必须写清基线与归因：

```text
本策略收益相对"逐行 gather/scatter 中转"基线；判据是搬运管线 + scalar 双降。
与 02 互补：连续用 02，gather/跨步用 03。叠加 01/02 时须相对"前序策略后"评估，避免基线错位。
```

## 检索卡（短卡）

动作：将逐行中转改为批循环，在连续UB累加器中紧凑gather，再批量scatter。
适用：适用于逐行或逐元素GM→UB→GM中转，且源或目的非连续的循环。
限制：跨批复用同一单缓冲累加器时，必须保持WAR/RAW同步顺序。
范围：kernel中的索引KV行gather及连续workspace写入。
检索词：连续UB累加器、批循环、gather、scatter、realIdx、workspace。
机会：按索引gather的非连续源行逐行中转，且每行伴随跨管线同步。
代价：需占用一块批量大小的连续UB缓冲区。
