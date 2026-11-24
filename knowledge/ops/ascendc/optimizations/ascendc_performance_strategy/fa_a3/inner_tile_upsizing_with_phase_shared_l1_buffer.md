---
type: Optimization
title: 放大内层 tile + 串行相位共享片上 buffer（摊销 per-tile 固定开销）
description: 放大内层tile，并让串行相位共享同一L1 buffer，替代每相位各占一份。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/05-inner-tile-upsizing-with-phase-shared-l1-buffer.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：放大内层 tile + 串行相位共享片上 buffer（摊销 per-tile 固定开销）

> **单一优化点：** 当一个分 tile 的 kernel 因 **tile 数过多**而受"每个 tile 的固定开销"（Cube scalar/同步、跨管线 `SetWaitFlag`、GM→L1 每 tile 重载、Vec 每 tile softmax 建状态）拖累时，把**内层/归约维 tile 放大整数倍**（如 KV 列维 tile 放大 2 倍，tile 数减半），直接削减 tile 数。放大的**容量障碍**用三招克服：(1) **串行相位共享 buffer**——两个**永不同时需要**的操作数（如 mm1 的 `K` 与 mm2 的 `V`）共用同一 L1 buffer，靠**既有的**跨管线 `SetWaitFlag<MTE1_MTE2>` 保证后相载入覆盖前相时前相已被消费；(2) **运行期定容** buffer（按 actual dims，非编译期 MAX）；(3) 用一个 `nBlocks=ceil(N/blockW)` 块循环包住原有单块计算，`nBlocks=1` 时与旧路径逐位等价。
>
> **算子无关性：** 本策略适用于**所有**分 tile 的 Cube/Vector kernel，只要存在"两个计算相位串行、各需一个互斥操作数"的结构（注意力 `Q@K^T`(K) → `P@V`(V)、两段式 GEMM、多段拼接等），或"buffer 按 MAX 预留而运行期远小于 MAX"的浪费。

本策略只改"内层 tile 大小 + 片上 buffer 的容量/共享方式 + 把单块计算包进块循环"。不改数学公式、scale、mask、累加顺序、输出 dtype/布局；不删任何同步（相位共享**依赖**既有 `SetWaitFlag`，见 §6.2）。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

很多分 tile kernel 的内层 tile 取保守小值（如 `s2Tile=128`），是因为**两个 buffer 各占一份**（mm1 的 `K` 与 mm2 的 `V` 各开一个 L1 buffer），按 MAX 维度预留，L1 预算被撑满。小 tile 导致 tile 数爆炸，每个 tile 都背负一份**与 tile 大小无关**的固定开销：

```text
for task in tasks:
  for s2Tile in CeilDiv(S_kv, s2Tile):          # tile 尺寸小、S_kv 长 ⇒ tile 数多
    Q = Load GM->L1 ; K = Load GM->L1 ; Mmad Q@K^T ; Fixpipe wsS
    softmax ; P = Load wsP->L1 ; V = Load GM->L1 ; Mmad P@V ; Fixpipe wsO
    # 每 tile 固定开销: 多条 SetWaitFlag、cube scalar(Alloc/EnQue/DeQue/Free)、
    #                   softmax 建 rowmax/rowsum 状态、wsS/wsP/wsO tile DMA
```

每 tile 的固定开销（跨管线 flag、scalar 循环/地址、softmax 状态建立、小 DMA）随 **tile 数**线性堆叠。tile 越小、`S_kv` 越长，开销占比越高。

典型症状：profiling 显示 `aic_scalar_time`、`aiv_scalar_time` 占比高，或 `MTE1_MTE2`/`MTE2_MTE1` flag 条数随 tile 数爆炸；放大 `s2Tile` 后 tile 数减半，这些条数直接腰斩。

### 1.2 本策略利用的机制

| 机制 | 利用方式 |
|---|---|
| Cube/Vec 固定开销随 tile 数 | tile 数 `/k`（k=放大倍数），per-tile scalar/flag/状态建立总量 `/k` |
| **串行相位互斥** | mm1（用 `K`）与 mm2（用 `V`）**严格串行**、从不同时需要 `K` 与 `V` ⇒ 一个 L1 buffer 先装 `K`（mm1 相）、后被 `V` 覆盖（mm2 相） |
| 既有跨管线 `SetWaitFlag` | mm2 的 `V` 载入前本就有 `SetWaitFlag<MTE1_MTE2>`（等 mm1 的 MTE1 完成），它**顺带**保证覆盖 `K` 时 `K` 已被 L0B 消费完 ⇒ 相位共享**无需新增同步** |
| 运行期定容 | L1 buffer 按 **actual dims**（`s2Tile × max(d_qk,d_v)`）而非编译期 MAX 预留，省掉 MAX 浪费，腾出放大空间 |
| 块循环回退 | `nBlocks=ceil(N/blockW)`：`blockW=s2Tile_old` 时 `nBlocks=1`（与旧单块逐位等价），`s2Tile_new` 时 `nBlocks=k`（同一份代码两用） |

核心改动——`s2Tile` 放大 + K/V 共享 buffer + 块循环：

```text
# 基线：K、V 各占一个 L1 buffer（按 MAX），tile 尺寸受预算限制只能取较小值
qL1(mTile×d_qk) + kL1(s2Tile_old×d_qk) + vL1(s2Tile_old×d_v) + pL1(mTile×s2Tile_old)
for s2Tile: <单块 mm1(K)> ; softmax ; <单块 mm2(V)>               # tile 数多

# 改写后：K(mm1)/V(mm2) 共享一个 sharedKV buffer，运行期定容，tile 放大 k 倍
qL1(mTile×d_qk) + sharedKV(s2Tile_new×max(d_qk,d_v)) + pL1(mTile×s2Tile_new)
for s2Tile: for nb in nBlocks(=k): <K[nb]->sharedKV; mm1> ; softmax
            for nb: <V->sharedKV(覆盖K); mm2>                     # tile 数 /k
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 分 tile 结构 | 存在可放大的内层/归约 tile（KV 列维、归约 K 维、序列块等），放大 `k` 倍后 tile 数 `/k` |
| 瓶颈归因 | profiling 显示 per-tile 固定开销（scalar、`SetWaitFlag` 条数、softmax 状态建立、小 DMA）随 tile 数堆叠、占比显著 |
| 相位互斥（若用共享 buffer） | 两个被合并的操作数（如 `K`/`V`）用于**严格串行**的相位，**永不同时**被需要；后相载入前存在既有的 `SetWaitFlag` 保证前相已消费完（§6.2） |
| 容量 | 放大后 L1 总占用 `+ margin ≤ L1_BUDGET`（§4.2）；运行期定容可缩小非放大维的浪费 |
| 尾块可控 | 放大后内层块循环的尾块（`N % blockW != 0`）有 `SetTail`/`min` 兜底；或在门控上要求 `S_kv % s2Tile_new == 0`（满块，避免 workspace 未写列垃圾，§6.4） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- 长 `S_kv`、大归约维、tile 数多（固定开销占比高）。
- 两个操作数串行互斥（可直接共享 buffer，省一份）。
- buffer 按 MAX 预留而运行期远小于 MAX（运行期定容即省空间）。

不适用或需先重构：

- 两个操作数**并行**需要（如某相位同时读 `K` 与 `V`）——不可共享，须各留 buffer（放大空间受限于两者之和）。
- 放大 tile 后 L1 即使共享 buffer 仍超预算 —— 须先缩其它维或改 buffer 深度（属另一策略）。
- 放大使尾块语义复杂且无法保证满块（`S_kv % s2Tile_new != 0`）又无 `SetTail` 兜底 —— 不放大或选能整除的倍数。
- 目标 case 瓶颈在 GM→L1 带宽或算力（非 per-tile 固定开销）——放大 tile 不直接命中（可能持平）。

---

## 3. tile 放大倍数与块循环

### 3.1 放大倍数选择

```text
s2Tile_new = s2Tile_old * k          # k = 2（最常见：tile 数减半）
# 约束:
#   1) L1 容量（§4.2）: 放大后总占用 + margin ≤ L1_BUDGET
#   2) 满块优先: S_kv % s2Tile_new == 0（消除尾块/未写列垃圾，§6.4）
#   3) 块循环上限: nBlocks = ceil(s2Tile_new / blockW) 在硬件/软件合理范围（如 1~4）
# 不能满足时退回 k=1（不放大），或选更小 k
```

放大优先取**能整除 `S_kv`** 的值（消除尾块）；不能整除时靠块循环的尾块 `min`/`SetTail` 兜底（§6.4），仍安全。

### 3.2 块循环：单块代码的泛化回退

把原"单块 mm1/mm2"包进 `nBlocks` 循环，使**同一份代码**兼容放大前后：

```text
nBlocks = CeilDiv(N_of_this_phase, blockW)     # blockW = s2Tile_old（如 128）
for nb in 0 .. nBlocks:
    nLocal = min(blockW, N - nb*blockW)        # 尾块
    nAlign = AlignUp(nLocal, C0)
    Load operand[nb] -> sharedL1(buffer 覆盖前一 nb)
    Mmad(M=mBase, K=Kdim, N=nLocal, ...)
    Fixpipe(wsSlot + nb*blockW, nAlign, ...)
# nBlocks=1（s2Tile_old）⇒ 与旧单块路径逐位等价；nBlocks=k（s2Tile_new）⇒ 放大
```

mm2 若已有 K-tile 归约循环，且其循环上限按实际 `kvRows` 动态，则 `kvRows=s2Tile_new` 时天然兼容（无需新循环）。

---

## 4. 数据与缓存布局

### 4.1 共享 buffer 的相位语义

| 相位 | buffer 内容 | 写者/读者 | 覆盖安全性 |
|---|---|---|---|
| mm1（`Q@K^T`） | `K`（第一相操作数） | MTE2 写 `K`→L1，MTE1 读 `K`→L0B | — |
| mm2（`P@V`） | `V`（覆盖 `K`） | MTE2 写 `V`→L1，MTE1 读 `V`→L0B | mm2 载 `V` 前的 `SetWaitFlag<MTE1_MTE2>` 保证 mm1 的 `K` 已被 L0B 消费完 ⇒ 覆盖安全 |

`Q`（mm1 L0A 源）与 `P`（mm2 L0A 源）各自独立 buffer，不参与共享（mm1/mm2 都读 L0A，但 `Q`/`P` 内容不同且时序不同；若容量紧张可另行分析是否可共享，不在本策略默认范围）。

### 4.2 容量核算（通用）

```text
L1_total = sizeof(T) * ( Q_rows*d_qk                          # Q
                       + s2Tile_new * max(d_phase1, d_phase2) # 共享 K/V（取两相列维 max）
                       + mBase * s2Tile_new )                 # P
assert L1_total + MARGIN <= L1_BUDGET                         # 910B = 512KB
```

放大 `s2Tile` 时 `sharedKV` 与 `P` 均线性增长，须重算。`max(d_phase1,d_phase2)` 保证共享 buffer 装得下两相中列维较大者（K 用 `d_qk`，V 用 `d_v`）。

### 4.3 运行期定容（省 MAX 浪费）

buffer 由编译期 MAX 常量改为运行期 `TilingData` 字段（actual dims）：

```text
# 旧（MAX，浪费）: pipe->InitBuffer(sharedBuf_, MAX_ELEMS * sizeof(T));
# 新（actual）:    pipe->InitBuffer(sharedBuf_, s2TileSize_ * kvColsMax * sizeof(T));
```

注意：与**硬编码 `c0Stride`** 关联的 buffer 须保持该 `c0Stride` 对应的行数（如 `Q` 的 NZ `c0Stride` 绑定一个固定行数，须与 Q load / L0A read 的 `colC0Stride` 一致），不可无脑按 `mBase` 缩容，否则越界（§6.3 / 陷阱 2）。当 `mBase` 小于该固定行数时，Q buffer 仍须按固定行数占用。

---

## 5. 实施步骤

### 5.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| Host tiling | `s2TileSize` 放大条件（容量 + 满块门控）；新增/派生 `s2TileSize` 传入 kernel；运行期 dims 传入 buffer 定容 |
| Kernel `InitBuffers` | K/V 两 buffer 合并为一个共享 `sharedBuf_`（运行期定容）；其余 buffer 按运行期 actual dims |
| Kernel mm1 | 单块 → `nBlocks` 块循环（§3.2）；`K[nb]` 载入共享 `sharedBuf_`；`Fixpipe` 列偏移 `nb*blockW` |
| Kernel mm2 | `V` 载入同一 `sharedBuf_`（覆盖 `K`，靠既有 `SetWaitFlag<MTE1_MTE2>`）；若已有 K-tile 动态循环则免改 |
| Vector softmax / mask | **通常不改**；但放大 tile 使 vec 内 chunk 数变化时须重审索引（§6.5 / 陷阱 3） |
| 数学/scale/mask/累加顺序/输出 | **不改** |

### 5.2 通用 mm1 块循环改写

```text
# 基线（单块，kvRows ≤ blockW）
Load K -> kL1 ; Mmad(Q,K,cL0, N=kvRows) ; Fixpipe(wsS[0], kvRowsAlign)

# 改写后（nBlocks 块，共享 sharedKV）
nBlocks = CeilDiv(kvRows, blockW)
for nb in 0 .. nBlocks:
    kvRowsLocal = min(blockW, kvRows - nb*blockW)
    kvRowsAlignLocal = AlignUp(kvRowsLocal, C0)
    SetWaitFlag<MTE1_MTE2>()                       # 等 mm1 上一 nb 的 MTE1 完成（且首次保护 L0A）
    Load K[s2Start+nb*blockW] -> sharedKV[0..)         # 覆盖前一 nb 的 K
    Load K 其余列段 -> sharedKV[dV*kvRowsAlignLocal ..)
    SetWaitFlag<MTE2_MTE1>()
    cL0 = AllocL0C()
    Mmad(Q, sharedKV, cL0, N=kvRowsLocal, init=(nb==0))
    EnQue/DeQue(cL0)
    Fixpipe(wsS[sSlotBase + nb*blockW], cL0, nSize=kvRowsAlignLocal)
    FreeL0C(cL0)
```

### 5.3 共享 buffer 的载入顺序（正确性关键）

mm2 载 `V` 覆盖 `K` 前，**必须**保留 mm2 入口处既有的 `SetWaitFlag<MTE1_MTE2>`（等 mm1 的 MTE1 把 `K` 搬进 L0B 完成）。相位共享的安全**完全依赖**这条既有同步——**不得**为"优化"删除或挪动它（§6.2）。

---

## 6. 正确性红线

### 6.1 块循环尾块

`nBlocks=CeilDiv(N,blockW)`，尾块 `nLocal=min(blockW, N-nb*blockW)`，`nAlign=AlignUp(nLocal,C0)`。`Fixpipe` 列数用 `nAlign`（L0C NZ 块对齐），`mSize` 用实际 `mBase`（不 pad，写 GM 不越界）。须 ceil（漏尾块见 陷阱 1）。

### 6.2 相位共享依赖既有同步

mm2 载 `V` 覆盖 `K` 的安全性来自 mm1→mm2 之间**既有的** `SetWaitFlag<MTE1_MTE2>`。本策略**不新增也不删除**任何跨管线同步；若该 flag 不存在，须先确认 mm1 的 `K` 已被 L0B 消费（加 `SetWaitFlag<MTE1_MTE2>`）再共享，否则覆盖未消费的 `K` → mm2 用错数据。

### 6.3 运行期定容与硬编码 c0Stride

buffer 按运行期 dims 定容时，须保证其 NZ `c0Stride`（行数）与所有 load/read 端的 `colC0Stride`/`dstNzC0Stride` 一致。与硬编码 `c0Stride`（固定行数）绑定的 buffer 不可按 `mBase` 缩容（陷阱 2）。

### 6.4 满块门控（避免 workspace 未写列垃圾）

放大后若 `S_kv % s2Tile_new != 0`，末 tile 的 workspace 行可能含未写列（tail garbage），被 vec 端按 `s2Tile_new` 行步长读取时引入垃圾。两条兜底：

- **门控**：仅 `S_kv % s2Tile_new == 0`（满块）时放大；否则退 `s2Tile_old`。
- 或 vec 端按实际 `kvRows=min(s2Tile_new, S_kv-s2Start)` 读取（`SetTail`），不读未写列。

常采用门控（满块才放大）以简化 vec 端。

### 6.5 放大 tile 改变分 chunk ⇒ 重审 vec 索引（陷阱 3 关键）

放大 `s2Tile` 会改变 vec 侧行块（chunk）的行数，使原本"单 chunk"成立的 vec 循环变成"多 chunk"（总行数超过单 chunk 行数）。任何**依赖 chunk 内行偏移**的索引——例如因果掩码的全局行号推导——若漏掉 chunk 基偏移（分块偏移），第 2+ chunk 的阈值会整体偏移 ⇒ 大量行 mask 错。**放大 tile 后必须重审所有"单 chunk 假设下正确"的 vec 索引**，把 chunk 基偏移补进全局行号推导（见 §7 陷阱 3）。

### 6.6 数值正确性

不改 scale、mask、累加顺序、输出 dtype/布局。`nBlocks=1` 时与旧路径逐位等价；`nBlocks>1` 时归约/累加按块顺序进行，浮点允许 ≤atol 微小差异。

---

## 7. 已知陷阱

### 陷阱 1：块数用 floor 除法漏尾块

问题：`nBlocks = N / blockW`（floor）。
触发：`N % blockW != 0`。
症状：末尾 `< blockW` 的列未被 mm1 计算，该 tile 输出缺列、mismatch。
修复：`nBlocks = CeilDiv(N, blockW)`，尾块 `min` 兜底（§6.1）。

### 陷阱 2：运行期定容缩了与硬编码 c0Stride 绑定的 buffer

问题：把 `Q` buffer 按 `mBase` 缩容，但 Q load / L0A read 的 `colC0Stride` 仍按绑定的固定行数寻址。
症状：实际行数小于该固定行数（如 GQA 折叠后单核处理的行数较小时）越界 / 数据踩踏。
修复：与硬编码 `c0Stride` 绑定的 buffer 固定该行数（§6.3）；只对**无 c0Stride 依赖**的 buffer（如共享 K/V）按运行期定容。

### 陷阱 3：放大 tile 使 vec 多 chunk，索引漏 chunk 基偏移（本策略常见的"隐藏解锁条件"）

问题：放大 `s2Tile` 使 vec 侧单 chunk 行数变小，总行数超出后变为 2+ chunk；因果掩码等索引的全局行号推导只含 tile 内局部偏移、漏掉 chunk 基偏移，第 2 chunk 起阈值整体偏移。
症状：大量行 mask 错（mismatch 集中在后续 chunk 的边界行），且**只在多 chunk vec**（放大后）出现——单 chunk（放大前）隐匿。
修复：全局行号推导补上 chunk 基偏移（相关阈值推导同步修正），逐 chunk 重算（§6.5）。此 bug 常是放大 tile 的**唯一前置阻塞**，修后才能去掉门控把放大推广到更多 layout。

### 陷阱 4：相位并行操作数强行共享

问题：误以为两操作数串行，实际某相位同时读 `K` 与 `V`（或两段拼接同时需要），仍共享一个 buffer。
症状：后载入覆盖前相正在用的数据，随机 mismatch。
修复：实施前证明两相**严格串行、互斥**（§2 / §4.1）；不互斥则各留 buffer。

### 陷阱 5：删/挪 mm2 入口的 SetWaitFlag 致覆盖未消费的 K

问题：为"减少 flag"删掉 mm2 载 `V` 前的 `SetWaitFlag<MTE1_MTE2>`。
症状：`V` 覆盖尚未被 L0B 消费的 `K`，mm1 用错/混合数据。
修复：保留该 flag（§6.2）；相位共享的安全**依赖**它，属"不得动"的既有同步。

### 陷阱 6：误判整体未提速为策略失效

问题：放大 tile 使 per-tile 固定开销下降，但整体耗时持平（瓶颈在 GM→L1 带宽或算力）。
诊断：剖 `aic_scalar`/`aiv_scalar` 与 `SetWaitFlag` 条数是否随 tile 数下降。下降即对固定开销生效；整体提速需叠加命中瓶颈的策略。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 瓶颈归因 | 是否 per-tile 固定开销（scalar/flag/softmax 状态/小 DMA）随 tile 数堆叠？剖 `aic_scalar`/`aiv_scalar`/flag 条数 |
| 放大维与倍数 | 放哪个 tile（KV 列/归约 K/序列块）、`k` 取值；`S_kv % s2Tile_new` 是否为 0 |
| 相位互斥 | 两操作数（K/V）是否严格串行、永不同时需要？mm2 载 V 前是否有既有 `SetWaitFlag<MTE1_MTE2>`（§6.2） |
| 容量 | 共享 + 运行期定容后 L1 总占用 + margin ≤ budget（§4.2 核算） |
| c0Stride 依赖 | 哪些 buffer 与硬编码 `c0Stride` 绑定、不可缩容（陷阱 2） |
| 块循环 | `nBlocks`、尾块 `min`/`SetTail` 落点；`nBlocks=1` 是否与旧路径逐位等价 |
| vec 分 chunk | 放大后 vec 侧单 chunk 行数是否变小 ⇒ 多 chunk vec？所有 chunk 内行偏移索引是否含 chunk 基偏移（陷阱 3） |
| 满块门控 | `S_kv % s2Tile_new != 0` 时门控退回还是 `SetTail` 兜底（§6.4） |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 删除或挪动 mm2 载 `V` 前的 `SetWaitFlag<MTE1_MTE2>`（相位共享依赖它，陷阱 5）。
- 把与硬编码 `c0Stride` 绑定的 buffer 按运行期 `mBase` 缩容（陷阱 2）。
- 用 floor 除法算 `nBlocks`（陷阱 1）。
- 把并行（同时需要）操作数强行共享一个 buffer（陷阱 4）。
- 放大 tile 后不重审 vec 多 chunk 索引（陷阱 3）。
- 改变数学/scale/mask/累加顺序/输出 dtype。

回退或缩小策略的条件：

- 容量核算超限（共享 + 运行期定容仍放不下）→ 缩 `k` 或退 `s2Tile_old`。
- 精度失败且定位到 陷阱 1/2/3 单一原因 → 修该原因后重试。
- `S_kv % s2Tile_new != 0` 且无 `SetTail` 兜底 → 门控退回 `s2Tile_old`。
- 剖析显示 per-tile 固定开销**未下降**（瓶颈在带宽/算力）→ 放大未命中，重新归因（区别于 陷阱 6 的"下降但整体持平"）。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>            # 编译算子
bash <build> --soc=<soc> --op=<op> --wheel    # 编译 pta
source <set_env>
pytest <op>/test/test_<op>.py                 # 精度
pytest <op>/test/test_<op>_perf.py            # 性能（生成 profiling）
```

精度：与基线一致（沿用算子既有 `atol/rtol`）。**必须覆盖**：`nBlocks=1`（`s2Tile_old`，逐位等价回退路径）、`nBlocks>1`（放大）、`S_kv % s2Tile_new != 0`（尾块）、多 chunk vec（causal，陷阱 3）、不同 dtype。

性能（**必须用 profiling 归因，覆盖放大前后两路径**）：

- 放大路径（`nBlocks>1`）：整体 `Task Duration` 下降，per-tile 固定开销指标（`aic_scalar`/`aiv_scalar`、`SetWaitFlag` 条数）随 tile 数 `/k` 下降。
- 回退路径（`nBlocks=1`，如不满足门控的 case）不劣化（与旧路径逐位等价）。

性能结论必须写清基线、放大倍数与归因：

```text
本策略收益相对"s2Tile_old + K/V 各占 buffer + MAX 定容"基线；判据是 per-tile 固定开销随 tile 数下降。
回退路径（nBlocks=1）逐位等价是硬指标（不是可选项）。放大 tile 常暴露 vec 多 chunk 索引 bug（陷阱 3），
修后才能把放大推广到更多 layout——该修复属正确性，不属独立性能策略。
后续命中带宽/算力瓶颈的策略须相对"本策略后"评估，不能回到 s2Tile_old 基线作增量起点。
```

## 检索卡（短卡）

动作：放大内层tile，并让串行相位共享同一L1 buffer，替代每相位各占一份。
适用：内层tile因两个L1 buffer各占一份容量而取保守小值。
限制：V覆盖K前须保留mm2入口既有同步；共享限串行互斥相位，放大tile须满足容量和满块门控。
范围：分tile Kernel中mm1的K与mm2的V所用L1 buffer。
检索词：内层tile、s2Base、L1 buffer、串行相位互斥、per-tile固定开销。
机会：tile数量多，per-tile scalar、flag和状态建立形成重复固定工作。
