---
type: Optimization
title: 多缓冲软流水，重叠 MTE 搬运与矩阵/向量计算
description: 引入多缓冲软流水，重叠MTE搬运与矩阵/向量计算；AIC先执行MM2(t-2)，再发射MM1(t)。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/02-multibuffer-soft-pipeline.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：多缓冲软流水，重叠 MTE 搬运与矩阵/向量计算

> **单一优化点：** 在已完成 QKV 双向两级分块和 L1 复用的 FlashAttention 类 kernel 上，将逐 KV outer block 的串行发射改为 `PRELAUNCH=2` 的错位软流水，并把 Cube 侧 K/P/V L1 与 L0C 改为多缓冲 TQue，使下一块的 MTE2 搬运与当前块的 Mmad/Fixpipe/Vector 计算重叠。
>
> **前序依赖：** 本策略以"两级分块 + L1 大块复用、单缓冲、无流水"的结构为基线；两级分块本身是独立的前序策略。

本策略只做多缓冲软流水。它不引入 MM1 转置加载、Q->L0A 单指令、MM2 大块加载、tiling 重算、workspace 重新布局或数学公式变化。

---

## 1. 优化原理

### 1.1 性能问题模式

前序的两级分块虽然减少了 K/V 重复搬运，但顶层仍是串行链：

```text
AIC:
  for t2 in kvOuterBlocks:
    ComputeMM1(t2)  -> SIG_S_READY
    ComputeMM2(t2)  waits SIG_P_READY

AIV:
  for t2 in kvOuterBlocks:
    ComputeVec1(t2) waits SIG_S_READY -> SIG_P_READY
    ComputeVec2(t2) waits SIG_O_READY
```

真实依赖链是：

```text
MM1(t) -> Vec1(t) -> MM2(t) -> Vec2(t)
```

但串行发射导致 `MM2(t)` 返回前不会发射 `MM1(t+1)`。因此 `t+1` 的 K/P/V 搬运无法与 `t` 的 Mmad/Fixpipe/Vector 计算重叠，`RING_SLOTS=3` 只承担存储槽作用，没有形成流水。

同时，前序基线的 Cube 侧 L1 使用裸 `TBuf<A1>`，靠大量 `SetWaitFlag<...>` 串起 MTE2、MTE1、M、FIX。`SetFlag` 紧跟 `WaitFlag` 等价于硬同步，会把块内搬运和计算完全序列化。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| 计算流水 | AIC 在同一 tick 先做落后块 `MM2(t-2)`，再发射当前块 `MM1(t)`；AIV 对称执行 `Vec2(t-2)` 与 `Vec1(t)` |
| 数据搬运 | 下一 KV 块的 K/P/V MTE2 搬运与当前块 Mmad/Fixpipe/Vector 计算重叠 |
| 片上存储 | K/P L1 使用深度 3 TQue，V L1 使用深度 2 TQue，L0C 使用深度 2 TQue |
| 核间协作 | 沿用 `SIG_S_READY/SIG_P_READY/SIG_O_READY` CrossCore flag，只改变发射时序 |
| 同步机制 | 用 TQue `AllocTensor/EnQue/DeQue/FreeTensor` 替换跨流水手工 barrier；保留必要 `PipeBarrier<PIPE_M>` |

一图总结：

```text
前序基线（串行）              本策略（软流水）
----------------             --------------------------------
MM1(t)                       MM1(t) leads MM2 by PRELAUNCH=2
wait Vec1(t)         ->       same tick: MM2(t-2) + MM1(t)
MM2(t)                       transfer(t) overlaps compute(t-2)
single K/V/P TBuf            K/P TQue depth 3, V TQue depth 2
L0C depth 1                  L0C TQue depth 2
manual SetWaitFlag           TQue handoff manages MTE<->M<->FIX
```

---

## 2. 适用条件与泛化边界

必须同时满足：

| 条件 | 要求 |
|---|---|
| 基线结构 | 已完成两级分块：QKV 双向两级分块、Q 大块常驻 L1、K/V/P 以 128 微块处理 |
| Tiling | `PRELAUNCH=2`，`RING_SLOTS=PRELAUNCH+1=3`，workspace 已按 3 槽预留 |
| KV 外层 | 每个 task 内存在 `kvOuterBlocks` 个 KV outer blocks，可按固定顺序错位发射 |
| CrossCore 协议 | 已有 `SIG_S_READY/SIG_P_READY/SIG_O_READY`，且 acquire/release 计数稳定 |
| L1/L0 容量 | 多缓冲后 L1、L0A、L0B、L0C 不超过硬件容量 |
| UB 容量 | Vec 侧 input/output/tmp/state buffer 不超过 UB；必要时 output queue 可退回深度 1 |
| 正确性基线 | 前序基线精度稳定通过，且无随机 hang、workspace 覆盖或 flag 计数错误 |

优先适用：

- `kvOuterBlocks >= 2`，存在可填充、稳态、排空的 KV outer block 流。
- profiling 显示 AIC 等 Vec1、AIV 等 O、MTE2/MTE1/M/FIX 串行等待明显。
- 两级分块改造已落地，需要继续回收剩余搬运与计算重叠机会。

不适用或需先处理：

- 两级分块尚未完成，仍是原始单级调度。
- `PRELAUNCH >= RING_SLOTS` 或 slot 数不足，会覆盖未消费 workspace。
- CrossCore flag 有分支漏发、多发或空 subblock 不发 P_READY。
- L0C 深度 2 超过目标硬件容量，或 UB 深度 2 编译期溢出。
- 目标混入 MM1 转置 helper、tiling 变化或同步删减策略，导致收益无法归因。

---

## 3. 必须保持不变的内容

以下内容来自前序的两级分块基线，不能在本策略中重构：

- QKV 双向两级分块：`mBaseSize/kvBaseSize/qOuterBlocks/kvOuterBlocks`。
- Q 大块常驻 L1；K/V/P 工作粒度保持 128 行微块。
- MM1 沿用基线选定的裸 `LoadData2D` 或等价基线路径，不新增 transpose helper。
- Vec 侧 online softmax 状态：`maxCache/sumCache/expCache/wsMeta/wsAccO` 按 `RING_SLOTS` 槽寻址。
- workspace slot size、tiling 公式、`WorkspaceQueue` 基本语义。
- 数学公式、scale、mask、online softmax 合并、输出 dtype、GM 布局。
- 跨 task 边界：流水只在单个 task 的 KV 维度内展开；不同 batch/head/qOuterIdx 之间不跨流水。

允许修改且仅允许修改：

1. 顶层 KV loop 发射顺序：串行 `MM1(t); MM2(t)` 改为错位软流水。
2. Cube 侧 buffer：K/P L1 改深度 3 TQue，V L1 改深度 2 TQue，L0C 改深度 2 TQue。
3. Cube 侧手工跨流水 `SetWaitFlag` 删除，改由 TQue 生命周期表达。
4. Vec 侧输出 queue 可从深度 1 升到 2；若 UB 溢出可回退到 1。
5. Vec1 的 `vecDealM==0` 分支必须补发 P_READY。

---

## 4. 顶层软流水模板

### 4.1 不变量

```text
PRELAUNCH = 2
RING_SLOTS = PRELAUNCH + 1 = 3
RING_SLOTS > PRELAUNCH
inflight KV blocks <= PRELAUNCH + 1 = 3
```

`RING_SLOTS > PRELAUNCH` 是安全覆盖的硬条件。`WorkspaceQueue::ProducerAcquire()` 不等待 free signal，依赖 3 槽足以覆盖最多 3 个在飞块。禁止把 `PRELAUNCH` 调到大于等于 `RING_SLOTS`。

### 4.2 AIC 侧循环

```cpp
LoadQ(bz, qHead, qRowStart, qRows);  // task 内只执行一次

for (uint32_t t = 0; t < kvOuterBlocks + PRELAUNCH; ++t) {
    if (t >= PRELAUNCH) {
        uint32_t o = t - PRELAUNCH;
        ComputeMM2(bz, kvHead, kvStart(o), kvBlockRows(o), qRows);
        // 内部 ConsumerAcquire(SIG_P_READY)，末尾 ProducerReleaseFix(SIG_O_READY)
    }

    if (t < kvOuterBlocks) {
        ComputeMM1(bz, kvHead, kvStart(t), kvBlockRows(t), qRows);
        // 末尾 ProducerReleaseFix(SIG_S_READY)
    }
}
```

同一 tick 中先执行 `MM2(t-2)` 再发射 `MM1(t)`。这样当前块的 Mmad/Fixpipe 与后续块的 MTE2 搬运有机会通过多缓冲重叠。

### 4.3 AIV 侧循环

```cpp
SetTaskContext(bz, qHead, qRowStart, qRows);

for (uint32_t t = 0; t < kvOuterBlocks + PRELAUNCH; ++t) {
    if (t >= PRELAUNCH) {
        uint32_t o = t - PRELAUNCH;
        uint32_t slot = o % RING_SLOTS;
        ComputeVec2(slot, o == 0, o + 1 == kvOuterBlocks);
        // 内部 ConsumerAcquire(SIG_O_READY)
    }

    if (t < kvOuterBlocks) {
        uint32_t slot = t % RING_SLOTS;
        ComputeVec1(slot, t == 0, kvBlockRows(t));
        // 内部 ConsumerAcquire(SIG_S_READY)，末尾 ProducerReleaseMte3(SIG_P_READY)
    }
}
```

### 4.4 prologue、steady、epilogue

| 阶段 | tick | 行为 |
|---|---|---|
| prologue | `0 .. PRELAUNCH-1` | 只发 `MM1/Vec1`，填充 S/P |
| steady | `PRELAUNCH .. kvOuterBlocks-1` | 每拍 `MM2(t-2)+MM1(t)`，`Vec2(t-2)+Vec1(t)` |
| epilogue | `kvOuterBlocks .. kvOuterBlocks+PRELAUNCH-1` | 只消费剩余 `MM2/Vec2` |

不要手写多套 prologue/epilogue 分支；统一 loop 上界 `kvOuterBlocks + PRELAUNCH` 可以避免漏发或多发 flag。

---

## 5. CrossCore 同步契约

三个信号语义不变：

```text
SIG_S_READY: AIC.MM1 产 S[t]  -> AIV.Vec1 消费
SIG_P_READY: AIV.Vec1 产 P[t] -> AIC.MM2 消费
SIG_O_READY: AIC.MM2 产 O[t]  -> AIV.Vec2 消费
```

`WorkspaceQueue` 原语保持：

| 原语 | 语义 |
|---|---|
| `ProducerAcquire()` | 返回 `head_ % DEPTH` 槽，不阻塞 |
| `ProducerReleaseFix()` | `CrossCoreSetFlag<..., PIPE_FIX>(id)` 后 `head_++` |
| `ProducerReleaseMte3()` | `CrossCoreSetFlag<..., PIPE_MTE3>(id)` 后 `head_++` |
| `ConsumerAcquire()` | `CrossCoreWaitFlag<..., PIPE_MTE2>(id)` 后返回 `tail_++ % DEPTH` 槽 |

强制配对规则：

```text
每个 signal 的 ProducerRelease 次数 == kvOuterBlocks
每个 signal 的 ConsumerAcquire 次数 == kvOuterBlocks
prologue 只 producer，不 consumer
epilogue 只 consumer，不 producer
```

AIC 每个 steady tick 的顺序：

```text
ConsumerAcquire(P[o]) -> ComputeMM2(o) -> ProducerReleaseFix(O[o])
ComputeMM1(t) -> ProducerReleaseFix(S[t])
```

AIV 每个 steady tick 的顺序：

```text
ConsumerAcquire(O[o]) -> ComputeVec2(o)
ConsumerAcquire(S[t]) -> ComputeVec1(t) -> ProducerReleaseMte3(P[t])
```

### 5.1 空 subblock 必须补 flag

当某个 AIV subblock 分到 0 行时，Vec1 仍必须消费 S 并发布 P：

```cpp
ComputeVec1(slot, isFirst, kvBlockRows):
    sSlot = sQueue.ConsumerAcquire();
    pSlot = pQueue.ProducerAcquire();
    if (vecDealM == 0) {
        pQueue.ProducerReleaseMte3();
        return;
    }
    ...
    pQueue.ProducerReleaseMte3();
```

否则 AIC 的 `MM2` 会永久等待 `SIG_P_READY`。Vec2 入口已经消费 O；`vecDealM==0` 时可以直接 return，不需要发布新信号。

---

## 6. Cube 侧多缓冲实施

### 6.1 Buffer 改造

| buffer | 前序基线 | 本策略 | 作用 |
|---|---|---|---|
| Q L1 | `TBuf<A1>` | 保持 `TBuf<A1>` | task 内只读常驻，不参与 ping-pong |
| K/P L1 | `TBuf<A1>` | `TQue<A1, 3>` | 覆盖 `PRELAUNCH=2` 下的在飞块 |
| V L1 | `TBuf<A1>` | `TQue<A1, 2>` | 普通 ping-pong |
| L0A | `TQue<A2,2>` | 保持 | MTE1->M |
| L0B | `TQue<B2,2>` | 保持 | MTE1->M |
| L0C | `TQue<CO1,1>` | `TQue<CO1,2>` | M->FIX，允许 Fixpipe 与下个 Mmad 重叠 |

K/P 合并为一个 A1 队列是为了让 MM1 的 K 和 MM2 的 P 共用同一类 L1 ping-pong 资源，并满足 `PRELAUNCH=2` 的最多 3 个在飞块。

### 6.2 L1 TQue 标准用法

生产端：

```cpp
LocalTensor<QType> l1 = kpQueL1.AllocTensor<QType>();
LoadNdGmToNzL1(l1, gmSrc, rows, cols, ld, dstNzC0Stride);  // MTE2
kpQueL1.EnQue(l1);                                        // MTE2 -> MTE1
```

消费端：

```cpp
LocalTensor<QType> l1 = kpQueL1.DeQue<QType>();            // wait MTE2
LoadNzL1ToZnL0B(bL0, l1[offset], ...);                      // MTE1
// 发起该 l1 对应的全部 L1->L0 读取后
kpQueL1.FreeTensor(l1);                                    // MTE1 -> MTE2 reuse
```

要求：

- `AllocTensor/EnQue/DeQue/FreeTensor` 必须成对。
- `FreeTensor` 只能在该 L1 slot 所有 L1->L0 读取发起之后执行。
- 不得绕过 queue 访问同一基础 L1 buffer。
- queue depth 必须覆盖连续 `EnQue` 而未 `DeQue/Free` 的最大数量。
- 删除手工 `MTE2_MTE1/MTE1_MTE2/MTE1_M/M_MTE1/M_FIX/FIX_MTE2` 时，必须确认 TQue 路径覆盖同一 tensor 生命周期。

### 6.3 L0C 双缓冲

```cpp
LocalTensor<float> cL0 = queL0C_.AllocTensor<float>();
for each reduce tile {
    Mmad(cL0, aL0, bL0, cL0, ..., cmatrixInitVal=isFirst);
    PipeBarrier<PIPE_M>();  // 多次 Mmad 累加同一 cL0 时保留
}
queL0C_.EnQue(cL0);
cL0 = queL0C_.DeQue<float>();
Fixpipe(cL0 -> GM/workspace);
queL0C_.FreeTensor(cL0);
```

`PipeBarrier<PIPE_M>` 保护同一 L0C 上多次 Mmad 累加顺序，不能删除。删的是跨流水手工事件，不是 `PIPE_M` 内部累加顺序。

---

## 7. Vec 侧适配

Vec 侧算法与状态寻址沿用前序基线：

- `slot = t % RING_SLOTS`
- `prevSlot = (slot + RING_SLOTS - 1) % RING_SLOTS`
- `maxCache/sumCache/expCache/wsMeta/wsAccO` 继续按 ring slot 和任务内全局行寻址
- `isFirst` 和 `isLast` 的语义仍对应当前 Q outer block 的 KV outer block 边界

允许改动：

1. Vec 输出 queue 从深度 1 改为深度 2，让 Vec 输出搬运与下一行块计算重叠。
2. 若 UB 初始化或编译失败，优先将输出 queue 回退为深度 1；不要缩小 softmax 工作 buffer 或状态 cache。
3. Vec1 的 `vecDealM==0` 分支必须补发 P_READY，见第 5.1 节。

禁止：

- 改变 online softmax 公式或状态布局。
- 把 `prevSlot` 改成基于 PRELAUNCH 的跨两槽读取。Vec1/Vec2 的 online 状态仍读取上一个 KV outer block。
- 用 subblock 局部行号访问 `wsAccO`、`expCache` 或 output GM。

---

## 8. 容量核算

以下按 fp16/bf16 元素 2 字节、`C0=16`、典型配置 `dim=128`、`mBaseSize=512`、`kvBaseSize=512` 作示例估算。

### 8.1 L1

| buffer | 深度 | 单槽 | 单槽字节 | 总字节 |
|---|---:|---:|---:|---:|
| Q L1 | 2 段 | `256 x 192` | 96KB | 96KB |
| K/P L1 | 3 | `128 x 256` | 64KB | 192KB |
| V L1 | 2 | `256 x 128` | 64KB | 128KB |
| 合计 | | | | 416KB |

`416KB <= 512KB`，典型 L1 容量下安全。Q 的 2 段是手工切分的 TBuf 区域，不是 TQue 深度。

若 `dim > 192` 或硬件 L1 小于 512KB，必须重算 Q_L1_COLS、K/P/V 单槽和总量。

### 8.2 L0

| buffer | 深度 | 单槽 | 单槽字节 | 总字节 | 上限 |
|---|---:|---:|---:|---:|---:|
| L0A | 2 | `128 x 128 half` | 32KB | 64KB | 64KB |
| L0B | 2 | `128 x 128 half` | 32KB | 64KB | 64KB |
| L0C | 2 | `128 x 128 float` | 64KB | 128KB | 128KB |

L0C 深度 2 恰好占满 128KB。不得把 MM1 的 `n` 微块或 MM2 的 `m` 微块放大到超过 128。

### 8.3 UB

| buffer | 深度 | 字节/槽 | 总字节 |
|---|---:|---:|---:|
| Vec1 输入 queue | 2 | 32KB | 64KB |
| Vec1 输出 queue | 2 | 32KB | 64KB |
| 临时 buffer | 1 | 32KB | 32KB |
| max/sum/exp cache | - | `3 x 2KB x 3` | 18KB |
| default/brcb/oPrev | - | - | about 12KB |
| 合计 | | | about 190KB |

`about 190KB <= 192KB`，余量很小。若编译期 `InitBuffer` 失败，优先回退输出 queue 深度为 1。

短 Q、`kvBaseSize=1024` 时，输入 queue 单槽仍固定 32KB，Vec1 行切分粒度自动缩小；不要放大 queue buffer。

---

## 9. 正确性红线

### 9.1 数据依赖

- `MM2(o)` 只能消费已由 `Vec1(o)` 发布的 P。
- `Vec2(o)` 只能消费已由 `MM2(o)` 发布的 O。
- `MM1(t)` 发布 S 后，`Vec1(t)` 才能消费。
- 同一 KV block 的生命周期仍是 `MM1 -> Vec1 -> MM2 -> Vec2`，软流水只改变不同 block 的发射重叠。

### 9.2 同步顺序

- 每个 signal 的 acquire/release 次数必须等于 `kvOuterBlocks`。
- `vecDealM==0` 的 Vec1 也必须执行 `ConsumerAcquire(S)` 和 `ProducerReleaseMte3(P)`。
- 保留跨核 CrossCore flag；不得替换为核内 TQue。
- 保留 `PipeBarrier<PIPE_M>` 以保护同一 L0C 多次 Mmad 累加。
- 删除任一手工 `SetWaitFlag` 前，必须说明对应 TQue handoff 覆盖了哪条 tensor 生命周期。

### 9.3 内存生命周期

- `RING_SLOTS > PRELAUNCH`，否则 workspace slot 可能被覆盖。
- K/P/V L1 slot 在所有 L1->L0 读取发起前不得 `FreeTensor`。
- L0C slot 在 Fixpipe 完成前不得被下一次 Mmad 复用。
- 不得绕过 TQue 直接访问已交给 queue 管理的 L1/L0 buffer。
- task 结束时 epilogue 必须排空所有在飞 KV block，下一 task 从干净状态开始。

### 9.4 边界与数值

- `kvOuterBlocks` 小时 prologue/epilogue 占比高，性能收益可能变小，但不能省略 epilogue。
- `isFirst/isLast` 仍按 KV outer block 序号判断，不能按 tick 判断。
- `slot=t%RING_SLOTS`，`prevSlot=(slot+RING_SLOTS-1)%RING_SLOTS`。
- 不改变前序基线的 Q outer block state reset、全局行坐标与状态重置要求（见两级分块策略）。

---

## 10. 实施步骤

### 10.1 修改文件

| 文件 | 修改内容 |
|---|---|
| `<op>_kernel.h` | 将 Process 内 KV loop 改为 `kvOuterBlocks + PRELAUNCH` 的错位循环 |
| `<op>_cube.h` | K/P L1 改 `TQue<A1,3>`，V L1 改 `TQue<A1,2>`，L0C 改 `TQue<CO1,2>`；删除跨流水手工 `SetWaitFlag` |
| `<op>_vec.h` | Vec 输出 queue 可改深度 2；Vec1 空 subblock 补发 P_READY |
| `<op>_tiling.h/.cpp` | 不改，除非发现 `PRELAUNCH/RING_SLOTS` 未按前序策略预留 |
| `workspace_queue.h` | 不改 |
| `matmul_tile.h` | 不改；不新增 MM1 transpose helper |

### 10.2 最小代码改动顺序

1. 在 `<op>_kernel.h` 只改顶层循环，暂时不删 Cube 手工 barrier，确认 flag 计数不死锁。
2. 在 `<op>_vec.h` 修复 `vecDealM==0` 补发 P_READY。
3. 在 `<op>_cube.h` 声明和初始化 K/P/V/L0C TQue 深度。
4. 将 K/P/V L1 加载改为 `AllocTensor -> Load -> EnQue -> DeQue -> L1ToL0 -> FreeTensor`。
5. 将 L0C 改为深度 2 TQue 的 `Alloc -> Mmad -> EnQue -> DeQue -> Fixpipe -> Free`。
6. 删除已被 TQue 生命周期覆盖的跨流水 `SetWaitFlag`。
7. 保留 `PipeBarrier<PIPE_M>`。
8. 编译、跑 basic 精度、跑性能；失败时按第 12 节定位。

### 10.3 删除手工同步的判定表

| 同步点 | 处理 |
|---|---|
| `MTE2_MTE1` after L1 load | 若同一 L1 tensor 通过 TQue `EnQue/DeQue` 交接，删除 |
| `MTE1_MTE2` before L1 reuse | 若复用由 TQue `FreeTensor/AllocTensor` 管理，删除 |
| `MTE1_M` / `M_MTE1` around L0A/L0B | 若 L0A/L0B 已走完整 TQue 生命周期，删除 |
| `M_FIX` / `FIX_MTE2` around L0C/Fixpipe | 若 L0C 已走完整 TQue 生命周期，删除 |
| `PipeBarrier<PIPE_M>` between accumulative Mmad | 保留 |
| CrossCore `ProducerRelease/ConsumerAcquire` | 保留 |
| wrapper 或条件编译无法展开的同步 | 保留 |

---

## 11. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 前序基线是否稳定 | 精度、性能基线是否可复现 |
| PRELAUNCH/RING | `PRELAUNCH`、`RING_SLOTS`、是否满足 `RING_SLOTS > PRELAUNCH` |
| signal 计数 | S/P/O 每个 signal 的 acquire/release 次数表达式 |
| 空 subblock | `vecDealM==0` 时 Vec1 如何补发 P_READY |
| L1 队列 | K/P/V 各自 TQue 深度、单槽大小、总 L1 字节 |
| L0 队列 | L0A/L0B/L0C 深度、是否超过硬件上限 |
| UB 队列 | input/output/tmp/state 字节数，溢出时回退策略 |
| 手工同步 | 每个待删 `SetWaitFlag` 的 TQue 替代证据 |
| 保留同步 | 哪些 `PipeBarrier`、CrossCore 或 wrapper 必须保留 |
| 修改范围 | 是否没有改 tiling、workspace、MM1 transpose、数学公式 |

任一项无法回答，不实施本策略。

---

## 12. 故障定位与回退条件

### 12.1 死锁或 TIMEOUT

优先检查：

1. `kvOuterBlocks + PRELAUNCH` loop 上界是否正确。
2. prologue 是否只 producer，epilogue 是否只 consumer。
3. `SIG_S_READY/SIG_P_READY/SIG_O_READY` 的 acquire/release 次数是否都等于 `kvOuterBlocks`。
4. `vecDealM==0` 的 Vec1 是否补发 P_READY。
5. 是否把 `PRELAUNCH` 调到了 `>= RING_SLOTS`。

### 12.2 精度失败

优先检查：

1. 是否误删了 `PipeBarrier<PIPE_M>`。
2. K/P/V L1 是否过早 `FreeTensor`，导致下一块覆盖未读完数据。
3. L0C 是否在 Fixpipe 完成前复用。
4. Vec 状态 `slot/prevSlot` 是否仍按相邻 KV block，而不是按 PRELAUNCH 偏移。
5. 前序基线的全局行坐标与 state reset 是否被破坏。

### 12.3 性能未提升

优先检查：

1. 顶层是否仍在 `MM1(t)` 后立即等待 `MM2(t)`。
2. Cube 侧是否仍有大量手工 `SetWaitFlag` 串行化 MTE/M/FIX。
3. L1/L0C 是否实际使用了多缓冲 TQue，而不是声明了 queue 但立即 DeQue/Free 形成同步。
4. `kvOuterBlocks` 是否太小，prologue/epilogue 摊薄收益。
5. 是否将收益错误对比到原始单级基线；本策略增量必须相对前序两级分块基线评估。

### 12.4 回退条件

- L0C 深度 2 超硬件容量：回退本策略，不放大微块。
- UB 溢出：先将 Vec 输出 queue 回退深度 1，再复测。
- 任一 CrossCore flag 计数无法静态证明：回退顶层错位循环。
- 需要修改 tiling/workspace 或引入 MM1 transpose helper 才能达成目标：拆成独立策略。

---

## 13. 验收标准

最小验证：

```bash
cmake --build <kernel-build-dir>
bash <evaluate_script> <op> basic
```

建议验证：

- 代表性 shape：覆盖 `kvOuterBlocks=1/2/3+`、短 Q、空 subblock、尾块。
- 精度：与前序基线同量级，与基线同容差，mismatch `0%`。
- 性能：相对前序两级分块基线应有明显下降；稳定复测且精度通过、无死锁，可判定本策略有效。
- 死锁压力：多轮重复运行高风险 case，排查非确定性 race。

结果记录必须包含：

```text
baseline: 前序两级分块 + L1 复用（单缓冲、无流水）
candidate: 多缓冲软流水
gain: (baseline_median - candidate_median) / baseline_median
excluded changes: MM1 transpose helper, Q->L0A single instruction, tiling/workspace changes
```

禁止为了追求更大收益在同一轮混入其他 main 差异；否则无法判断本策略是否独立有效。

## 检索卡（短卡）

动作：引入多缓冲软流水，重叠MTE搬运与矩阵/向量计算；AIC先执行MM2(t-2)，再发射MM1(t)。
适用：已完成QKV双向两级分块和L1复用的FlashAttention kernel。
限制：MM2只能消费Vec1已发布的P。
范围：FlashAttention的逐KV outer block路径。
检索词：QKV双向两级分块、Q常驻L1、PRELAUNCH=2、MM1、MM2、MTE。
机会：分块与L1复用已存在，但顶层仍按KV outer block串行执行。
