---
type: Optimization
title: QKV 双向两级分块与 L1 复用
description: 由每个Q微块重复加载全量K/V，改为Q大块常驻L1并让128行K/V微块复用于多个Q微块
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/01-qkv-two-level-l1-reuse.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：QKV 双向两级分块与 L1 复用

> **单一优化点：** 将 FlashAttention 类 AscendC kernel 从“Q 微块外层、KV 微块内层、每个 Q 微块重复加载全量 K/V”的单级调度，改为 Q 方向和 KV 方向都带外层大块的两级分块。Q 大块在任务内常驻 L1，K/V 的 128 行微块在同一任务内被多个 Q 微块复用，从而减少 GM 到 L1 的重复搬运。
>
> **算子无关性：** 适用于所有存在“多个消费者重复读取同一组 KV”的 attention 类前向，不限于特定注意力变体；也可推广到任意“外层迭代重复装载同一右操作数”的两级分块场景。

本策略只做两级分块和 L1 复用。流水线、double buffer、TQue 多缓冲、搬运-计算重叠、语义未证明的 MM1 转置 helper、Q 到 L0A 单指令路径都不是本策略范围；这些必须作为独立策略评估。

---

## 1. 优化原理

### 1.1 性能问题模式

低效基线通常使用固定 128 微块：

```text
for qBlock in qSeqLen step 128:
  for kvBlock in kvSeqLen step 128:
    load K[128, dim] from GM to L1
    S = Q[128, dim] * K^T
    load V[128, dim] from GM to L1
    O += P[128, 128] * V
```

在 `qSeqLen=1024, dim=128` 时，每个 head 有 8 个 Q 微块和 8 个 KV 微块。由于每个 Q 微块都遍历全部 KV，K/V 各被从 GM 重复搬运 8 次；理论下界是每个 KV tile 在同一复用范围内只搬一次。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 片上存储 | Q 大块常驻 L1；K/V 128 行微块在任务内被多个 Q 微块复用 |
| 数据搬运 | 减少 K/V 的 GM->L1 重复搬运次数，降低 MTE2 带宽和地址计算开销 |
| 计算流水 | 本策略不引入软流水；仍按 `MM1 -> Vec1 -> MM2 -> Vec2` 串行同步 |
| 核间协作 | 沿用原有 AIC/AIV `WorkspaceQueue` 与 CrossCore flag，不改变跨核协议 |
| 同步机制 | 只保留单缓冲 L1 覆盖所需同步；不删除跨核或 queue 同步 |

核心改变是任务粒度：

```text
task = (batch, kvHead, group, qOuterIdx)
qRows <= mBaseSize
kv outer block rows <= kvBaseSize

for each task:
  LoadQ(qRows x dim) once into L1
  for each KV outer block:
    run MM1 over all Q microblocks
    run Vec1
    run MM2 over all Q microblocks
    run Vec2
```

例如 `qSeqLen=1024`、`mBaseSize=512` 时，4 个 128 行 Q 微块合并进一个任务，同一 K/V-128 微块随 2 个 Q 外层任务搬入，而不是随 8 个 Q 微块搬入。

---

## 2. 适用条件与泛化边界

必须同时满足：

| 条件 | 要求 |
|---|---|
| 算子形态 | Attention-like 前向，存在 `QK -> softmax/state -> PV -> output` 阶段 |
| Q/K/V 布局 | GM 中 Q/K/V/O 为 ND 行优先，形如 `[batch, heads, seq, dim]` 或可等价寻址 |
| 分块约束 | `mBaseSize % BLOCK_M == 0`，`kvBaseSize % BLOCK_N == 0`，`BLOCK_M=BLOCK_N=128` 保持不变 |
| dim 约束 | 常见 `dim=128`、`BASE_K=128`；若 `dim % BASE_K != 0`，必须显式处理 dim 尾块 |
| L1 容量 | Q 常驻、K/V/P 工作块峰值必须小于目标硬件 L1 容量 |
| UB 容量 | Vec1 必须按行切分（按 UB 容量导出每块行数），单次 S/P/softmax buffer 不得超过 UB |
| 状态连续 | 同一 Q outer block 内的 KV outer blocks 按顺序处理，online softmax 状态可用 `isFirst/isLast` 表示 |
| 基线稳定 | 修改前 build、精度、性能可重复；否则不能归因策略收益 |

优先适用：

- `qSeqLen` 明显大于 `BLOCK_M`，K/V 被多个 Q 微块重复读取。
- `dim <= 192` 或 Q 常驻 L1 后仍有足够 L1 空间容纳 K/V/P 工作块。
- profiling 显示 GM->L1 搬运、MTE2 等待或 K/V 重复加载占比明显。
- 后续还计划叠加流水策略；两级分块可作为后续多缓冲软流水的结构前提。

不适用或需先重构：

- K/V 复用范围被跨核切开，且没有正确的跨分片 online softmax 合并。
- `kvBaseSize` 放大后 Vec 侧无法满足 UB、32B 对齐或 softmax tiling 约束。
- Q/K/V 布局不是连续 ND，且没有可靠的 GM offset 和 NZ 搬运契约。
- 当前实现已有 workspace slot、CrossCore flag、subblock 写回或 softmax 状态错误。
- 目标收益来自 MM1 转置加载、TQue 多缓冲或 barrier 删除；这些不是本策略。

---

## 3. Tiling 选择规则

新增 host/kernel 共享字段：

```cpp
uint32_t mBaseSize;      // Q 外层大块行数
uint32_t kvBaseSize;     // KV 外层大块行数
uint32_t qOuterBlocks;   // ceil(qSeqLenAlign / mBaseSize)
uint32_t kvOuterBlocks;  // ceil(kvSeqLen / kvBaseSize)
```

保留基线已有 `seqBlocks/kvLoops/tailValid/...` 字段，避免破坏结构体布局。建议 tiling 字段类型统一为 `uint32_t`，并让 host 侧写入顺序与 kernel `CopyTiling` 完全一致。

推荐选择函数：

```text
SelectS2BaseSize(qSeqLen, groupNum):
  # 上限 1024：保证 vec1ChunkRows = UB_QUEUE_BYTES/(kvBaseSize*4) >= 8，
  # softmax state 写入地址保持 32B 对齐；UB 192KB 下 kvBaseSize>1024 会超限
  if qSeqLen <= 16: return 1024
  else:             return 512

SelectMBaseSize(qSeqLen, kvBaseSize):
  base = 512
  if qSeqLen <= 16:
    if   kvBaseSize <= 512:  base = 512
    elif kvBaseSize <= 1024: base = 256
    elif kvBaseSize <= 2048: base = 128
    else:                    base = 64
  return max(base, BLOCK_M)
```

派生值：

```text
qOuterBlocks  = ceil(qSeqLenAlign / mBaseSize)
kvOuterBlocks = ceil(kvSeqLen / kvBaseSize)
totalGSq      = groupNum * qOuterBlocks
totalBNkv     = batch * nkv
usedCoreNum   = min(totalBNkv * totalGSq, MAX_CORES)
```

核间分配继续使用原来的线性切分逻辑，例如 `bNkvEnd[]/gSqEnd[]`。不要在本策略中改变核数策略或跨核任务归属。

---

## 4. 数据与缓存布局

### 4.1 L1 布局

所有 L1 张量按 `LoadNdGmToNzL1` 生成的 NZ/zN 布局存放，`C0=16`，fp16/bf16 元素按 2 字节估算。

| 缓存 | 推荐布局 | 用途 |
|---|---|---|
| Q L1 | 单段连续，`qRowsAlign = AlignUp(qRows, C0)`，`dstNzC0Stride=qRowsAlign` | 任务开始时加载一次，被所有 KV outer blocks 复用 |
| K L1 | `BLOCK_N x dimAlign`，默认 128 行微块 | MM1 右矩阵；保持基线 K 加载形态 |
| V L1 | `BLOCK_N x dimAlign`，默认 128 行微块 | MM2 右矩阵；保持基线 V 加载形态 |
| P L1 | `BLOCK_M x KP_L1_COLS`，推荐 `KP_L1_COLS=256` | MM2 左矩阵，来自 workspace_P |

Q L1 寻址必须使用任务内行偏移。不要再用“前 256 行/后 256 行”的隐式双段切换，除非实现中已明确封装为等价的全局行寻址。

### 4.2 容量核算

单缓冲路径（符号化核算，按目标 shape 代入）：

```text
Q 常驻: mBaseSize * dimAlign * sizeof(T)
K 当前块: BLOCK_N * dimAlign * sizeof(T)
V 当前块: BLOCK_N * dimAlign * sizeof(T)
P 块: BLOCK_M * KP_L1_COLS * sizeof(T)
MM1 峰值: Q + K
MM2 保守峰值: Q + P + V      # 最大峰值，必须 < L1 容量
```

若后续加入 double buffer 或放大 K/V 单次 L1 行数，必须重新核算。

Vec 侧 UB 主路径（按 192KB 量级 UB 估算）：

```text
Vec1 输入 queue buffer + 输出 queue buffer + 临时 buffer: 各 32KB 量级
max/sum/exp state cache: RING_SLOTS * 2KB * 3 量级
softmax default buffers: 数 KB
总占用必须 < UB 容量
```

若 `kvBaseSize` 增大，必须通过对 Vec1 的行切分粒度控制单次 UB 占用。

---

## 5. 实施步骤

### 5.1 修改位置

| 文件 | 修改内容 |
|---|---|
| `<op>_tiling.h/.cpp` | 增加 `mBaseSize/kvBaseSize/qOuterBlocks/kvOuterBlocks`，计算 workspace 尺寸 |
| `<op>_kernel.h` | 将任务从 `(seqBlock, kvLoop)` 改为 `(qOuterIdx, kvOuterIdx)` |
| `<op>_cube.h` | Q 常驻 L1；MM1/MM2 改成外层 KV block + 内层 128 微块 |
| `<op>_vec.h` | Vec1/Vec2 适配 `mBaseSize x kvBaseSize` workspace、行切分、状态 cache |
| `workspace_queue.h` | 通常不改；只确认 slot size 与 head/tail 语义仍一致 |
| `matmul_tile.h` | 通常不改；必须先做 helper capability inventory，函数名只作为候选示例，不把普通 B helper 直接迁移到 MM1 K^T |

### 5.2 Host 侧 workspace 放大

所有 per-slot 尺寸从 `BLOCK_M/BLOCK_N` 换成 `mBaseSize/kvBaseSize`：

```text
wsSSize    = RING_SLOTS * mBaseSize * kvBaseSize * sizeof(float)
wsPSize    = RING_SLOTS * mBaseSize * kvBaseSize * qElementSize
wsOSize    = RING_SLOTS * mBaseSize * dimAlign   * sizeof(float)
wsMetaSize = RING_SLOTS * mBaseSize * 3          * sizeof(float)
wsAccOSize = RING_SLOTS * mBaseSize * dimAlign   * sizeof(float)
perCoreBytes = wsSSize + wsPSize + wsOSize + wsMetaSize + wsAccOSize
totalWsBytes = perCoreBytes * usedCoreNum
```

按目标 shape 代入核算总量；workspace 尺寸随 `mBaseSize/kvBaseSize` 平方级增长，须确认不超过可用 GM workspace。这是 GM workspace，占用 HBM；不是 UB/L1。

### 5.3 Kernel 顶层调度

```cpp
for each task (bz, kvHead, groupId, qOuterIdx) assigned to this core {
    qHead = kvHead * groupNum + groupId;
    qRowStart = qOuterIdx * mBaseSize;
    qRows = min(mBaseSize, qSeqLen - qRowStart);

    if ASCEND_IS_AIC {
        cube.LoadQ(bz, qHead, qRowStart, qRows);
    }
    if ASCEND_IS_AIV {
        vec.ResetSoftmaxState();  // 每个 Q outer block 开始必须重置
        vec.SetTaskContext(bz, qHead, qRowStart, qRows);
    }

    for (uint32_t t2 = 0; t2 < kvOuterBlocks; ++t2) {
        kvStart = t2 * kvBaseSize;
        kvBlockRows = min(kvBaseSize, kvSeqLen - kvStart);

        if ASCEND_IS_AIC {
            cube.ComputeMM1(bz, kvHead, kvStart, kvBlockRows, qRows);
        }
        if ASCEND_IS_AIV {
            vec.ComputeVec1(t2 % RING_SLOTS, t2 == 0, kvBlockRows);
        }
        if ASCEND_IS_AIC {
            cube.ComputeMM2(bz, kvHead, kvStart, kvBlockRows, qRows);
        }
        if ASCEND_IS_AIV {
            vec.ComputeVec2(
                t2 % RING_SLOTS,
                t2 == 0,
                t2 + 1 == kvOuterBlocks);
        }
    }
}
```

本策略可以保持 PRELAUNCH 字段存在，但不要依赖 PRELAUNCH 做错位发射；多缓冲软流水属于后续策略。

### 5.4 MM1：`S = Q * K^T`

输出 `S` 是 `qRows x kvBlockRows`，写入 `workspace_S` 当前 slot，列跨度 `outerCols=kvBaseSize`。

必须先建立 helper capability inventory，再选择实现路径。策略中的函数名只是候选示例，
不是跨算子的稳定 API；当前算子没有同名 helper 或 helper 语义不匹配时，必须使用
显式 AscendC primitive fallback。

| required capability | 数学阶段 | 源逻辑布局 | 目标逻辑语义 | 候选实现 / fallback | 禁止误用 |
|---|---|---|---|---|---|
| `gm_nd_to_l1_nz` | K/Q/V/P staging | GM ND tile | L1 NZ tile | 本地 `LoadNdGmToNzL1` 或等价 DataCopy/LoadData 路径 | 不得假设所有算子都有同名 helper |
| `l1_to_l0a_regular_A` | MM1 / MM2 左矩阵 | L1 NZ left tile | L0A Zz left operand | 本地 `LoadNzL1ToZzL0A` 或等价 primitive | 不得只凭名称跳过 src/dst layout 证明 |
| `l1_to_l0b_k_transposed_for_qk` | MM1 `Q * K^T` | `K_L1[kvRows, dim]` | `L0B[dim, kvRows]` | 若本地 helper 明确支持 K^T 源布局则复用；否则用显式 `LoadData` / `LoadData2DParams` 参数实现 | 不得把普通 B 矩阵 helper 当作 K^T helper |
| `l1_to_l0b_regular_B_for_pv` | MM2 `P * V` | `V_L1[kvRows, dim]` | 普通右矩阵 `L0B[kvRows, dim]` | 本地 `LoadNzL1ToZnL0B` 或等价 primitive | MM2 可用不证明 MM1 K^T 可用 |
| `l0c_to_gm_nd` | Fixpipe | L0C NZ result | GM/workspace ND result | 本地 `FixpipeNzL0cToNdGm*` 或等价 Fixpipe | 需证明 stride/shape 与 workspace slot 一致 |

MM1 K 加载的硬约束：

- 如果 K 在 L1 的源布局仍是 `[kvRows, dim]`，MM1 需要的是 K^T，即 L0B 逻辑语义
  `[dim, kvRows]`。
- 普通右矩阵 B helper（例如某些实现中的 `LoadNzL1ToZnL0B`）只在证明它支持上述
  K^T 源布局时才能用于 MM1；它在 MM2 `P * V` 的 V 加载中成功，不构成 MM1 证据。
- 没有本地等价 helper 时，优先使用显式 `LoadData2DParams` fallback，并在实现计划中
  写清 `repeatTimes/srcStride/dstGap/ifTranspose` 与 C0 分块关系。
- 若策略文档、参考实现或 CODE_MAP 只给出 helper 名称，designer/codegen 必须把该名称
  降级为候选，先在当前源码中确认定义和语义。

```cpp
ComputeMM1(bz, kvHead, kvStart, kvBlockRows, qRows):
    sSlot = sQueue.ProducerAcquire();
    outerCols = kvBaseSize;
    nL1Size = BLOCK_N;
    kTiles = ceil(dim, BASE_K);

    for (nL1Start = 0; nL1Start < kvBlockRows; nL1Start += nL1Size) {
        kvRows = min(nL1Size, kvBlockRows - nL1Start);
        kvRowsAlign = AlignUp(kvRows, C0);
        kOffset = ((bz * nkv + kvHead) * kvSeqLen + kvStart + nL1Start) * dim;
        kvL1 = Load K[kvRows, dim] GM -> L1(NZ), dstNzC0Stride=kvRowsAlign;

        for (mL0Start = 0; mL0Start < qRows; mL0Start += BLOCK_M) {
            mRows = min(BLOCK_M, qRows - mL0Start);
            mRowsAlign = AlignUp(mRows, C0);

            cL0 = L0C.Alloc();
            for (ki = 0; ki < kTiles; ++ki) {
                aL0 = load Q slice from qL1[mL0Start] -> L0A;
                bL0 = load K slice from kvL1 -> L0B using
                      capability l1_to_l0b_k_transposed_for_qk;
                Mmad(cL0, aL0, bL0,
                     m=mRowsAlign, n=kvRowsAlign, k=BASE_K,
                     cmatrixInitVal=(ki == 0));
            }
            Fixpipe cL0 -> sSlot[mL0Start * outerCols + nL1Start],
                mSize=mRows,
                nSize=kvRowsAlign,
                srcStride=mRowsAlign,
                dstStride=outerCols;
        }
    }
    sQueue.ProducerReleaseFix();
```

单缓冲 L1 正确性要求：

- 覆盖 K L1 buffer 前，必须确认上一 K 微块全部 L1->L0 读取已完成。
- 本 K 微块的所有 Q 微块和 K-tile 读取都发起后，才允许下一次 GM->L1 覆盖。
- 该同步只保护 L1 生命周期，不改变 `WorkspaceQueue` 的 S/P/O 计数。

### 5.5 MM2：`O = P * V`

输入 `P` 来自 `workspace_P` slot，形状 `qRows x kvBlockRows`，列跨度 `kvBaseSize`。输出 `O` 写 `workspace_O` slot，列跨度 `dimAlign`。

```cpp
ComputeMM2(bz, kvHead, kvStart, kvBlockRows, qRows):
    pSlot = pQueue.ConsumerAcquire();
    oSlot = oQueue.ProducerAcquire();
    outerCols = kvBaseSize;
    KL1_SPLIT = BLOCK_N;

    for (mL0Start = 0; mL0Start < qRows; mL0Start += BLOCK_M) {
        mRows = min(BLOCK_M, qRows - mL0Start);
        mRowsAlign = AlignUp(mRows, C0);
        cL0 = L0C.Alloc();
        isFirstK = true;

        for (kL1Start = 0; kL1Start < kvBlockRows; kL1Start += KL1_SPLIT) {
            kL1Size = min(KL1_SPLIT, kvBlockRows - kL1Start);
            kL1SizeAlign = AlignUp(kL1Size, C0);

            pL1 = Load P[pSlot + mL0Start * outerCols + kL1Start] -> L1(NZ),
                  dstNzC0Stride=mRowsAlign;
            vOffset = ((bz * nkv + kvHead) * kvSeqLen + kvStart + kL1Start) * dim;
            vL1 = Load V[kL1Size, dim] GM -> L1(NZ),
                  dstNzC0Stride=kL1SizeAlign;

            aL0 = LoadNzL1ToZzL0A(pL1, mRowsAlign, kL1SizeAlign, mRowsAlign);
            bL0 = LoadNzL1ToZnL0B(vL1, kL1SizeAlign, BASE_K, kL1SizeAlign);
            Mmad(cL0, aL0, bL0,
                 m=mRowsAlign, n=BASE_K, k=kL1SizeAlign,
                 cmatrixInitVal=isFirstK);
            isFirstK = false;
        }

        Fixpipe cL0 -> oSlot[mL0Start * dimAlign],
            mSize=mRows,
            nSize=BASE_K,
            srcStride=mRowsAlign,
            dstStride=dimAlign;
    }
    oQueue.ProducerReleaseFix();
```

V 仍按 128 行工作块加载。本策略的收益来自同一任务内多个 Q 微块复用 K/V，不来自放大 V 单次 L1 粒度。

### 5.6 Vec1：scale、mask、online softmax、P 写回

Vec1 处理 `mBaseSize x kvBaseSize` 的 S slot，但必须按行分块进入 UB：

```text
vec1ChunkRows = floor(VEC_QUEUE_BUF_SIZE / (kvBaseSize * sizeof(float)))
vec1ChunkRows = align_down_or_up_to_safe_multiple(vec1ChunkRows, 8)
```

例：UB 队列 buffer 32KB、`kvBaseSize=512`、fp32 时为 16 行，满足 32B 对齐。`kvBaseSize` 不能大到使 `vec1ChunkRows < 8`，否则 softmax state 写入地址可能不满足 32B 对齐。

```cpp
ComputeVec1(slot, isFirst, kvRows):
    sSlot = sQueue.ConsumerAcquire();
    pSlot = pQueue.ProducerAcquire();
    outerCols = kvBaseSize;

    for (chunkRow = 0; chunkRow < vecDealM; chunkRow += vec1ChunkRows) {
        dealRows = min(vec1ChunkRows, vecDealM - chunkRow);
        mGlobal = vecStartM + chunkRow;

        sUb = copy S[sSlot + mGlobal * outerCols], shape=(dealRows, outerCols);
        Muls(sUb, smScale);

        stateBase = slot * stateStride + mGlobal;
        prevSlot = (slot + RING_SLOTS - 1) % RING_SLOTS;
        prevStateBase = prevSlot * stateStride + mGlobal;

        SoftMaxShapeInfo:
            srcM = dealRows
            srcK = outerCols
            oriSrcK = kvRows

        SoftMaxFlashV2(
            sUb,
            sumCache[stateBase],
            maxCache[stateBase],
            sUb,
            expCache[stateBase],
            isFirst ? defaultState : prevStateBase,
            smTiling,
            srcShape);

        pHalf = Cast(sUb -> fp16);
        copy pHalf -> P[pSlot + mGlobal * outerCols];
    }
    pQueue.ProducerReleaseMte3();
```

必须使用 `oriSrcK=kvRows` 处理 KV 尾块，让 softmax 只归约有效列。不要保留基线 128 列手写 `-inf` mask 逻辑。

### 5.7 Vec2：online O 累加、归一化与写回

```cpp
ComputeVec2(slot, isFirst, isLast):
    oSlot = oQueue.ConsumerAcquire();
    prevSlot = (slot + RING_SLOTS - 1) % RING_SLOTS;
    mChunk = clamp_to_brcb_multiple(VEC_QUEUE_BUF_SIZE / dimAlign, max=255);

    for each row chunk:
        globalRow = vecStartM + rowOffset;
        oNewUb = copy O_tile[oSlot + globalRow * dimAlign];

        if (!isFirst) {
            oPrevUb = copy wsAccO[prevSlot, globalRow];
            expBrcb = Brcb(expCache[slot, globalRow]);
            RowMuls(oPrevUb, oPrevUb, expBrcb);
            Add(oNewUb, oNewUb, oPrevUb);
        }

        if (isLast) {
            sumBrcb = Brcb(sumCache[slot, globalRow]);
            RowDivs(oNewUb, sumBrcb);
            FinalizeOutputChunk(oNewUb, globalRow);  // 输出收尾写回，使用全局行坐标
        } else {
            copy oNewUb -> wsAccO[slot, globalRow];
        }
```

`maxCache/sumCache/expCache` 每个 ring slot 使用固定 `stateStride = AlignUp(mBaseSize, 32)`，不能使用当前 subblock 的 `vecDealM`。所有 GM、workspace、state、exp-meta、output 写回都必须使用同一任务内全局行坐标 `globalRow/mGlobal`。

---

## 6. 正确性红线

### 6.1 数据依赖与同步顺序

- `S` 必须先由 MM1 完整写入并 `ProducerReleaseFix()`，Vec1 才能 `ConsumerAcquire()`。
- `P` 必须先由 Vec1 写入并 `ProducerReleaseMte3()`，MM2 才能 `ConsumerAcquire()`。
- `O_tile` 必须先由 MM2 写入并 `ProducerReleaseFix()`，Vec2 才能 `ConsumerAcquire()`。
- 单缓冲 L1 覆盖前必须等待上一块 L1->L0 读取完成。
- 不得删除 CrossCore flag、WorkspaceQueue acquire/release 或承担 L1 生命周期的同步。
- 不得把本策略和“删除冗余同步”混在同一实验里。

### 6.2 内存生命周期

- Q L1 在一个 task 内常驻，只读，task 结束后可覆盖。
- K/V/P L1 工作块只能在所有消费者发起读取后覆盖。
- `wsS/wsP/wsO/wsAccO/wsMeta` slot size 必须由 host 和 kernel 使用同一公式。
- ring slot 只按 `slot = t2 % RING_SLOTS` 访问；上一状态按 `prevSlot=(slot+RING_SLOTS-1)%RING_SLOTS`。
- `stateStride` 必须固定为按 `mBaseSize` 对齐后的值。

### 6.3 边界处理

- Q 尾块：`qRows = min(mBaseSize, qSeqLen - qRowStart)`。
- KV 尾块：`kvBlockRows = min(kvBaseSize, kvSeqLen - kvStart)`。
- micro tile 尾块：所有 `mRows/kvRows/kL1Size` 均用 `min` 和 `AlignUp(C0)`。
- output 写回必须 clamp 到有效 `qSeqLen`，不能写 padding 行。
- softmax 使用 `oriSrcK=kvRows` 屏蔽 padding 列。
- `dim % BASE_K != 0` 时必须实现 K 维尾块；不能假设所有 shape 都是 dim=128。

### 6.4 数值正确性

- 不改变 scale、mask、online softmax 更新公式、累加顺序和输出 dtype。
- `isFirst` 表示当前 Q outer block 的第一个 KV outer block。
- `isLast` 表示当前 Q outer block 的最后一个 KV outer block。
- Q outer block 切换时必须重置 softmax 状态；不能继承上一个 Q outer block 的 `max/sum/exp`。
- 不要把向量批量状态改成大量 `SetValue/GetValue` 标量循环，除非只用于初始化极少量默认值。

---

## 7. 已知陷阱

### 7.0 Precision-safe host/kernel contract（GQA 必须执行）

两级分块放大的是逻辑 tile；它不会自动放大 host 侧的输入 mask 存储，也不会让
Vec1 的 `outerCols` 变成有效列数。对 GQA，以下契约必须在 host/plugin、tiling、
kernel 和 Vec1 四处同时成立：

```text
maskKvSeqLen = ceil(kvSeqLen / kvBaseSize) * kvBaseSize
maskStorage  = qStorage * maskKvSeqLen
mask[row, col] = maskBase + row * maskKvSeqLen + col
validCols    = min(kvBlockRows, kvSeqLen - kvStart)
```

- host/plugin 必须按 `maskKvSeqLen` 分配和填充 mask，并把同一个值写入 tiling；禁止
  用原始 `kvSeqLen` 作为已经 padding 的 mask 行跨度。
- kernel/Vec1 读取 mask 时必须使用绝对行地址 `row * maskKvSeqLen`；不能把 mask
  当成紧凑的 `qStorage * kvSeqLen`，也不能用 subblock 局部行号代替 task 内全局行号。
- `outerCols=kvBaseSize` 只是 S/P/workspace 的存储跨度；softmax 的有效归约列必须
  是当前 tile 的 `validCols`，并传入 `oriSrcK`。S、P、mask 的 tail 搬运若不能证明
  2D `DataCopy` 的 stride/gap 单位，必须使用显式逐行 GM offset 的 fallback。
- GQA 的 head 映射必须保持 `qHead = kvHead * groupNum + groupId`；不得把 FA 的
  `groupNum=1` 或单个 qHead 的实验结果外推到 GQA。

### 7.1 Precision gate before performance

策略实施必须先按风险维度完成精度门禁，再进行 profiling 或性能调参。
最小分阶段顺序为：

1. host/plugin/tiling 静态契约：mask storage/stride、workspace slot、`outerCols`、
   `qHead` 映射必须能逐项对应到 kernel 字段。
2. `MM1 -> Vec1 -> MM2 -> Vec2`：先确认 S、mask/softmax、P、O 的阶段边界和读写
   地址；失败时优先 dump S（softmax 前）和 mask，不要把最终 O mismatch 直接归因于
   evaluator。
3. 精度 case 必须覆盖并单独记录：跨 mask tile、高 Q-head/group、BF16/高任务数、
   大 head dim、长序列/多 KV tile 等边界组合。任何一个 case 失败都阻止策略采纳。
4. kernel 运行时错误（执行异常、DDR 越界等）不能被标记为评测框架导入错误，
   也不能用导入成功掩盖。

精度通过后才允许执行性能抽样。性能 case 从精度 case 集中确定性选择并覆盖主要
shape 类别；性能结论必须同时给出各 case 的中位数和加权统计。

### 7.2 MM1 intermediate-tensor hard gate（两级大块必须执行）

两级分块放大的是逻辑 tile；若 MM1 的 `Mmad -> L0C -> Fixpipe -> GM` 链路出现
周期性零值/垃圾值，该问题会在进入 softmax 后被放大成最终 O mismatch。因此最终 O
的小误差或 softmax 参数检查不能替代 MM1 中间张量证据。

在继续性能 profiling 之前，必须完成以下门禁：

1. 在多组 `mBaseSize/kvBlockRows` 配置（小/中/大块各一）中，至少对第一个
   `nL1Start=0,mL0Start=0` tile 记录 MM1 的 `S`。优先记录 Fixpipe 后 GM 的 S；若
   工具链允许，再同时记录 L0C/Fixpipe 前后的数据。
2. 将 `S` 与同一 Q/K tile 的 `Q@K^T` golden 对比，并记录 case、tile 坐标、stride、
   非零/坏值摘要。出现周期性零值、未初始化大值或 Fixpipe 后才出现的差异时，
   失败分类必须指向 MM1 S 损坏，不能归因于 softmax、精度容差或 evaluator。
3. `S` 未通过时，禁止只修改 Vec1/softmax/Vec2 后继续跑性能；连续相同 failure
   signature 时必须升级为 MM1 stage isolation，并保留每次实验的 diff 和回滚证据。
4. 调试代码必须使用当前 AscendC 支持的 dtype/API；未验证的 debug helper 不得带入
   correctness gate。编译失败的 debug 改动不能被记录为修复成功。
5. 缺少上述中间张量证据时，策略状态只能是 blocked/needs_fix，不能是 adopted，
   即使部分精度 case 通过或源码结构看起来符合策略。

### 陷阱 1：Subblock 写回偏移坐标系错误

问题：输出写回 GM 时使用 subblock 内局部偏移，而不是任务内全局行 `mGlobal/globalRow`。

症状：

- 第二个 AIV subblock 整段写错地址。
- mismatch 约一半行。

修复：

- 全程只使用一个任务内全局行变量。
- 写回入参命名为 `globalRow`。
- 输出地址使用任务内 Q 行起点 + `globalRow`，再按 `qSeqLen` clamp。

### 陷阱 2：Q outer block softmax 状态污染

问题：Vec 侧 softmax 状态 buffer（`max/sum/exp` cache）跨 Q outer block 未重置。

触发条件：

- `qOuterBlocks > 1`，即 `qSeqLen > mBaseSize`。

症状：

- mismatch 约一半行。
- 误差呈 bimodal 分布，前半正确、后半错误。
- 第二个及后续 Q outer block 继承前一个 block 的 softmax 状态。
- `qSeqLen <= mBaseSize` 的 shape 可能正常。

修复方式 A：给 Vec1 入口增加 `isFirstQBlock` 参数，在第一个 KV outer block 前重置状态。

```cpp
if (isFirstQBlock) {
    maxCache.SetValue(-INFINITY);
    sumCache.SetValue(0.0f);
    expCache.SetValue(0.0f);  // 或按实现需要设为 1.0f
}
```

修复方式 B：增加 `ResetSoftmaxState()`，在每个 task 开始时调用。

```cpp
__aicore__ inline void ResetSoftmaxState() {
    maxCache.SetValue(-INFINITY);
    sumCache.SetValue(0.0f);
    if (expCache.GetSize() > 0) {
        expCache.SetValue(0.0f);
    }
}
```

诊断步骤：

1. 检查每个 Q outer block 开始前是否调用 reset。
2. 对比第一个和第二个 Q outer block 的初始 `max/sum`。
3. 若只在 `qSeqLen > mBaseSize` 时失败，优先排查本问题。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 当前基线结构 | Q/KV 循环顺序、`BLOCK_M/BLOCK_N/BASE_K`、workspace slot 尺寸 |
| 目标 shape | `batch, heads, kvHeads, qSeqLen, kvSeqLen, dim, dtype` |
| tiling 选择 | `mBaseSize/kvBaseSize/qOuterBlocks/kvOuterBlocks` 和选择原因 |
| L1 容量 | Q/K/V/P 峰值字节数，是否小于目标硬件 L1 |
| UB 容量 | `vec1ChunkRows`、input/output/tmp/state 字节数，是否小于 UB |
| workspace | `wsS/wsP/wsO/wsMeta/wsAccO` per-core 和 total 字节数 |
| MM1 K 加载 | helper capability inventory；K 源布局、L0B 目标语义、是否需要显式 `LoadData2DParams` fallback |
| 同步保护 | 单缓冲 L1 覆盖前后由哪个同步保证 |
| 行坐标 | `mGlobal/globalRow/vecStartM/qRowStart` 的定义和传递路径 |
| 状态重置 | 每个 Q outer block 开始如何重置 softmax state |
| 尾块 | Q/KV/dim/输出 padding 如何处理 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 在同一轮加入多缓冲软流水、TQue 深度调整、同步删减、语义未证明的 MM1 转置加载或新的 matmul helper。
- 改变数学公式、scale、mask、online softmax 合并公式、输出布局或 dtype。
- 改变跨核任务划分，除非同时实现跨核归约。
- 用 subblock 局部行号写 GM 输出或状态 cache。
- 让 host 和 kernel 使用不同的 workspace slot size。
- 因某个小 shape 通过就跳过长序列、尾块和多 Q outer block 测试。

出现以下情况应回退或缩小策略：

- L1/UB 容量核算超过硬件限制。
- basic 精度失败，且无法定位到单一坐标系、状态 reset 或尾块问题。
- 编译失败来自 tiling struct 布局不一致。
- 性能与基线持平，profiling 显示 K/V GM->L1 搬运没有下降。
- 需要依赖当前源码不存在或语义未证明的 MM1 transpose helper 才能编过；应改用显式 primitive fallback 或拆成独立策略。

---

## 10. 验收标准

最小验证：

```bash
cmake --build <kernel-build-dir>
bash <evaluate_script> <op> basic
```

建议验证：

- 代表性 shape：覆盖 `qSeqLen <= 16`、`qSeqLen <= mBaseSize`、`qSeqLen > mBaseSize`、`kvSeqLen` 非 `kvBaseSize` 倍数、尾行/尾列、不同 `groupNum`、不同 dtype。
- 精度：与原基线同容差，mismatch `0%`。
- 性能：相对原始单级基线应有可测下降；若低于 1% 或持平，必须用 profiling 检查 K/V GM 搬运是否仍重复。
- 重复运行高风险 case，排查 §7 陷阱 1/2 的非确定性或半段错误。

性能结论必须写清楚基线：

```text
本策略收益相对原始单级基线；
后续多缓冲软流水必须相对"本策略后"的结果评估，
不能回到原始单级基线作为后续增量的起点。
```

## 检索卡（短卡）

动作：由每个Q微块重复加载全量K/V，改为Q大块常驻L1并让128行K/V微块复用于多个Q微块
适用：具有QK→softmax/state→PV→output阶段的Attention-like前向
限制：S必须由MM1完整写入并执行ProducerReleaseFix后才能进入后续阶段
范围：FlashAttention类AscendC前向kernel
检索词：QKV两级分块、L1复用、GM→L1、QK、softmax/state、PV
机会：Q微块外层、KV微块内层的单级调度使每个Q微块重复加载全量K/V
