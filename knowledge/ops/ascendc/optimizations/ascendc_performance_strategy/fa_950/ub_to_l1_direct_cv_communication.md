---
type: Optimization
title: UB→L1 直通（消除 CV 通信的 GM 中转往返）
description: 将Vector侧中间数据由UB经GM中转到L1，改为UB→L1直通，消除GM往返。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/10-ub-to-l1-direct-cv-communication.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-23T06:46:32Z'
platforms:
- '950'
---

# 性能优化策略：UB→L1 直通（消除 CV 通信的 GM 中转往返）

> **单一优化点：** 在 Cube-Vector 协同（CV）算子中，若 Vector 侧产出的中间数据要交给 Cube 侧做矩阵乘，传统写法是**两段式** `UB →(MTE3)→ GM(workspace) →(MTE2/Nd2Nz)→ L1`。Ascend 950PR/950DT（arch35 / dav-3510）**新增了 UB→L1 硬通道**，可让 Vector 直接把数据送进 L1，Cube 直接消费，**全程不经 GM**——省掉一次 GM 写 + 一次 GM 读，以及对应的 workspace 容量。
>
> **这条约束是有时效性的**：许多既有算子里写着「禁 UB→L1，须两段式」之类的红线（本例中记为 `RK-C04`），那是 **220x 架构**的限制。官方架构变更文档明确写了 351x 新增该通路：
> > *「新增 UB 到 L1 Buffer 的数据通路 —— 支持将数据直接从 UB 搬运到 L1 Buffer，而无需先从 UB 搬运到 GM，再从 GM 搬运到 L1 Buffer」*
>
> **移植旧算子到 A5 时，应主动复查这类红线是否已过期。**
>
> **状态：✅ 37/37 精度通过（2026-08-13）。UB→L1 CV 直通链路完全打通。**
>
> **三个关键修复（反复失败的根因，其他算子移植 CV 通路时务必注意）**：
> 1. **UB 内 ND→NZ 必须用 `Copy()` 接口**（向量格式转换，V pipe），**不是 `DataCopy(Nd2NzParams)`**（后者是 GM→L1 的接口，UB→UB 会 errcode81 越界或产出不同 NZ 物理）
> 2. **Copy(V pipe) → DataCopyParams(MTE3 pipe) 之间必须 `SetWaitFlag<V_MTE3>()`**（RAW 同步）
> 3. **单缓冲跨批/跨 Gather 必须加 `SetWaitFlag<MTE3_V>()`**（WAR 同步：DataCopy 读完 ubNz → 下一批 Copy 可覆写）
>
> 缺第 1 条 errcode81/全错；缺第 2 条 flaky；缺第 3 条多 task ring 流水时 mismatch 4~55%。三者齐全则 37/37 稳定通过。
>
> **▶ 工程落地续篇（2026-08-12）**：[`11-cv-path-migration-buffer-manager.md`](./cv_path_migration_buffer_manager.md) 用 arch35 完整参考实现（`SFAPmaster/.../arch35/`）的实证，给出「当前 no-CV 架构 → BufferManager 直通」的 **4 阶段迁移路线**，并逐一破解本策略 §2.0 的 TPipe 约束与 V3 的容量双重排除。实施前先读 11；本策略仍是约束/陷阱的权威来源。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

CV 协同算子的典型数据流：

```text
AIV: 计算/gather → UB ──(MTE3)──→ GM(workspace) ──跨核 flag──→ AIC: GM ──(MTE2)──→ L1 → L0 → Mmad
                                   ↑                                    ↑
                              一次 GM 写                            一次 GM 读
```

代价有三重：

| 代价 | 说明 |
|---|---|
| 一次 GM 写 | 占 Vector 侧 MTE3 |
| 一次 GM 读 | 占 Cube 侧 MTE2 |
| workspace 容量 | 需为该中间数据分配 GM，且常按 ring slot 数倍增；**工作集过大还会跨出缓存产生双峰**（见配套策略「分块粒度自适应」§6） |

而这份数据**只是核间传递**，本身并不需要在 GM 里落地。

### 1.2 A5 上的新通路

| 通路 | 950PR/950DT | 数据类型 |
|---|---|---|
| `VECIN/VECCALC/VECOUT → TSCM`（UB→L1） | √ | 含 `half`/`bfloat16_t`/`float` 等 |
| 随路 ND2NZ 的 `Local→Local` 版本 | √ | 同上 |

即存在两种写法：

```cpp
// (a) 普通搬运：UB 侧已按 NZ 交织排布时使用
DataCopy(l1Tensor[dstOff], ubTensor, dataCopyParams);

// (b) 随路 ND2NZ：UB 侧是 ND 连续时使用，搬运同时完成格式转换
DataCopy(l1Tensor[dstOff], ubTensor, nd2nzParams);
```

---

## 2. ⚠️ 必须遵守的约束（都是实测踩出来的）

### 2.0 🔴 AIC/AIV 的 TPipe InitBuffer 序列必须对称

`TPipe` 的 buffer 分配隐式决定 event ID 分配。AIC 和 AIV 两侧的 `InitBuffer` 调用序列必须**完全对称**，否则 event ID 偏移导致 `SetFlag`/`WaitFlag` 错配。**解法**：在 kernel 层（AIC/AIV 都执行）统一 `pipe->InitBuffer<TBuf<A1>>` + `Get()` 分发视图。不需 BufferManager，不需改 Cube 侧现有 `TQue<A1>`。

```cpp
// kernel 层（AIC/AIV 都执行）—— 保证两侧 InitBuffer 序列对称
pipe->InitBuffer(sharedL1Buf_, l1Size);
LocalTensor<T> l1View = sharedL1Buf_.Get<T>();
if ASCEND_IS_AIC { cube.SetL1View(l1View); }
if ASCEND_IS_AIV { vec.SetL1View(l1View); }
if ASCEND_IS_AIC { cube.InitBuffers(pipe); }
if ASCEND_IS_AIV { vec.InitBuffers(pipe); }
```

> **最小修复不需要引入 BufferManager**——kernel 层 `InitBuffer<TBuf<A1>>` + `Get()` 分发视图即可；BufferManager（§2.1）是另一种成熟写法，并非唯一解法。
> Cube 侧的 `TQue<A1>`/`TBuf<A1>` 不需改，由 TPipe 顺序分配，不冲突。
> 注：§7.1 D2g/D2h 的「AIV 侧多一次 `InitBuffer` 即失败」是**探针基线**（仅 MM1 吃 L1、MM2 仍走 GM）下的结论，不能直接外推到最终合入形态；最终合入的是本节写法，并按 §7 验收表 37/37 通过。

### 2.1 L1 必须由**一处**统一分配，不能两侧各自 `InitBuffer`

**这是最容易踩、且报错最具误导性的一条。**

```cpp
// ❌ 错误：AIV 与 AIC 各自 InitBuffer 同一逻辑 buffer
if ASCEND_IS_AIV { pipe->InitBuffer(buf_, size); }   // 各自向 TPipe 申请 L1 额度
if ASCEND_IS_AIC { pipe->InitBuffer(buf_, size); }   // → 分配冲突
// 症状：device error 507015，且【小 shape 可能侥幸通过】，误导为"容量问题"

// ✅ 正确：kernel 层统一分配一次，把 tensor 视图分发给两侧
pipe->InitBuffer(sharedL1Buf_, size);                 // 只此一处
LocalTensor<T> view = sharedL1Buf_.Get<T>();
if ASCEND_IS_AIC { cubeKernel_.SetL1View(view); }
if ASCEND_IS_AIV { vecKernel_.SetL1View(view); }
```

成熟实现（`ops-transformer` 的 `BufferManager<BufferType::L1>`）的做法是：
**用一个 `TBuf<A1>` 一次性 `InitBuffer` 整块 L1，然后自己按 offset 切分**，`AllocBuffer()` 只是移动内部游标并返回 tensor 视图——从机制上杜绝了重复分配。

### 2.2 L1 的 TPosition 用 `A1`，不是 `TSCM`

虽然文档的通路表里写的是 `→ TSCM`，且 `TSCM` 的物理内存确实就是 L1 Buffer，但成熟实现用的是 **`TPosition::A1`**：

```cpp
// buffer_manager.h 首行注释：
// L1  TPosition::A1
// L0A TPosition::A2
// L0B TPosition::B2
// L0C TPosition::CO1
// UB  TPosition::VECIN
```

原因：手写 Cube 路径下 `LoadData`(L1→L0) 系列**只接受 `A1/B1/B2`**（`Load2D` 明确：仅支持 `GM→A1; GM→B1; A1→A2; B1→B2`）。用 `TSCM` 会在 L1→L0 这一环断链。

> `TSCM` 主要服务于 **Matmul 高阶 API** 的 `SRC_POSITION` 机制（`A/B 矩阵 POSITION=TSCM` + `SRC_POSITION=VECOUT`）。手写 Cube 不走那套注册，用 `A1` 即可。

### 2.3 跨核 flag 必须挂在**正确的 pipe** 上（改路径就要改 pipe）

**这一条是 §7 端到端失败的最可能根因，务必在改造时同步修改。**

两段式与直通式的**生产者 pipe 与消费者 pipe 都不同**：

| 路径 | AIV 侧写入用的 pipe | AIC 侧读取用的 pipe |
|---|---|---|
| 两段式 `UB→GM→L1` | MTE3（写 GM） | **MTE2**（`Nd2Nz` GM→L1） |
| 直通 `UB→L1` | MTE3（UB→L1 也走 MTE3） | **MTE1**（`LoadData` L1→L0） |

即：**AIV 侧的 set pipe 不变（都是 MTE3），但 AIC 侧的 wait pipe 必须从 `MTE2` 改成 `MTE1`。**

```cpp
// ❌ 直通改造后仍沿用原 wait：
CrossCoreWaitFlag<MODE, PIPE_MTE2>(kselReady);   // MTE2 队列在等
// ... 后面直接 LoadData(L1→L0)，这是 MTE1 指令 ——
//     MTE1 不受该 flag 约束，可在数据落地前就发射 ⇒ 读到上一 slot 残留

// ✅ 正确：
CrossCoreWaitFlag<MODE, PIPE_MTE1>(kselReady);
CrossCoreWaitFlag<MODE, PIPE_MTE1>(kselReady + AIV1_OFFSET);   // 双 AIV 各一次
SetWaitFlag<HardEvent::MTE1_MTE2>();   // 若同 task 内还有 GM 装载，一并拦在 flag 之后
```

成熟实现（`buffer.h` 的 `Buffer<BufferType::L1>::SetCrossCore/WaitCrossCore`）正是这样写的：
AIV `CrossCoreSetFlag<4, PIPE_MTE3>(id0)`；AIC `CrossCoreWaitFlag<4, PIPE_MTE1>(id0)` + `(id0+16)`。
其 `buffer_mix_core.h` 亦注明 *「L1 buffer 的生产者为 MTE2 或者 MTE3，消费者为 MTE1」*。

> **症状特征**：精度全错、无 device error，**且与 shape 无关**——
> 连 `nTiles==1 && kTiles==1`（所有切片偏移恒为 0）的最小用例也失败。
> 这正是区分「同步问题」与「NZ 偏移问题」的判据：
> **偏移问题只会在需要切片的 shape 上出现；同步问题在最小 shape 上也出现。**

### 2.4 需要编译选项 `ENABLE_CV_COMM_VIA_SSBUF=true`

> *「当 `ENABLE_CV_COMM_VIA_SSBUF` 配置为 true 时，使用 SSBuffer 进行通信，数据通过 UB→L1 Buffer 之间的**硬件通道**搬运（推荐）；当为 false 时，数据搬运到 L1 **经过 GM**」*
>
> *「**默认开关关闭**」*、*「使用 DataCopy 接口从 UB 拷贝数据到 L1 Buffer」属于需要打开的场景*

**不开这个选项，代码语法上成立、功能也正确，但底层仍走 GM——等于白改，性能不会变。**

配置方式（文档样例）：
```cmake
ascendc_compile_definitions(<target> PRIVATE ENABLE_CV_COMM_VIA_SSBUF=true)
```
注意不同构建体系的宏注入方式不同（若工程用 ASC 编译器，上述宏可能不适用，需确认实际生效方式，或在 kernel 源码顶部 `#define`）。

**验收时必须确认它真的生效**：若改造后 `mte3`/`mte2` 时间未下降，首先怀疑此选项未打开。

---

## 3. 适用条件

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 目标平台 | Ascend 950PR / 950DT（arch35）。220x 不支持 |
| 数据流形态 | Vector 产出 → Cube 消费，中间数据仅用于核间传递，无需 GM 落地 |
| L1 容量 | Cube 侧现有 L1 占用 + 新增驻留量 ≤ L1 总容量。**必须按 ring slot 数计算**（见 §4.2） |
| 布局契约 | Vector 写入的布局与 Cube 消费的布局必须严格一致（见 §5，这是最难的一环） |
| 同步 | 具备跨核同步手段（`CrossCoreSetFlag/WaitFlag` 或等价封装） |

不适用：

- 该中间数据**还需被其它核/后续 kernel 读取**（那就必须在 GM）
- L1 容量放不下（可考虑分块，但会显著增加复杂度）
- 220x 等不支持该通路的平台

---

## 4. 实施步骤

### 4.1 host 侧：按 L1 实测余量下发开关

**禁止在 kernel 里硬编码容量假设**（RK-B01）。host 侧查询平台真实 L1 大小：

```cpp
uint64_t l1Size = 0;
platform_ascendc::PlatformAscendC p(platformInfo);
p.GetCoreMemSize(platform_ascendc::CoreMemType::L1, l1Size);

// 逐项对应 kernel 侧 InitBuffers，改动需同步
const uint64_t l1UsedBytes  = /* Cube 侧现有各 L1 buffer 之和 */;
const uint64_t newNeedBytes = (uint64_t)RING_SLOTS * rows * colsAlign * dtypeSize;
uint32_t directL1 = (l1Size > 0 && l1UsedBytes + newNeedBytes <= l1Size) ? 1u : 0u;
tiling.set_directL1(directL1);   // l1Size==0（平台信息缺失）时保守退回两段式
```

保留退化路径（`directL1==0` 走原两段式），使大 shape 仍可工作。

### 4.2 容量必须按 ring slot 数算

若原 workspace 是 `RING_SLOTS` 个槽轮转，L1 也**必须**分配同样多的槽：
ring 流水中 `Gather(cur)` 与 `MM1(cur)` 之间隔着其它阶段，单槽会被后续 task 覆写。

```cpp
pipe->InitBuffer(l1Buf_, (uint32_t)RING_SLOTS * rows * colsAlign * sizeof(T));
```

> **实测预算参考**（本例 512KB L1）：Cube 侧已占约 92KB（GQA, G=4）~400KB（MLA, G=128）。
> GQA 场景余量 420KB、3 槽只需 384KB → 放得下；
> MLA 场景余量仅 112KB、3 槽需 1536KB → 放不下，必须退化或分块。
> **这类"同一算子不同 shape 结论相反"的情况很常见，务必逐 shape 核算。**

### 4.3 Vector 侧：写入 L1（✅ 实战验证，37/37 通过）

**三步式写法**（arch35 CopyKvNdToNz + CopyOutKvUb2L1 的正确移植）：

```cpp
if (directL1_ == 1) {
    // 步骤 1：Copy() UB ND→UB NZ（V pipe，17-stride 防 bank 冲突）
    // ⚠️ 必须用 Copy，不能用 DataCopy(Nd2NzParams)——后者是 GM→L1 接口，UB→UB 会 errcode81
    Copy(ubNz, ubTensor[r * dkAlign], dkAlign, dealRows,
         {17, 1, 1, static_cast<uint16_t>(dkAlign / 16)});

    // 步骤 2：V→MTE3 RAW 同步（Copy 写完 ubNz → DataCopy 可读）
    SetWaitFlag<HardEvent::V_MTE3>();

    // 步骤 3：DataCopyParams UB NZ→L1（MTE3 pipe，去 17-stride padding）
    DataCopyParams dcp;
    dcp.blockCount = dkAlign / 16;            // 列块数
    dcp.blockLen = dealRows;                   // 每列块行数
    dcp.srcGap = 17 - dealRows;                // UB 17-stride gap
    dcp.dstGap = dstNzC0Stride - dealRows;     // L1 NZ 行 gap
    DataCopy(l1View_[slotBase + row * C0], ubNz, dcp);

    // 步骤 4（单缓冲时必须）：MTE3→V WAR（DataCopy 读完 ubNz → 下一批 Copy 可覆写）
    SetWaitFlag<HardEvent::MTE3_V>();
} else {
    DataCopy(wsGm_[dstOff], ubTensor, count);  // 退化：原两段式
}
```

**DataCopyParams 参数单位**：blockLen/srcGap/dstGap 都是 **DataBlock (32B)**，不是元素或字节。

**Copy dataCount 限制**：`Copy()` 的 dataCount（每 repeat 元素数）有上限。dk=128 OK，dk=576 超限 → **dk > 128 时必须分段 Copy（tileSize=128）**。

### 4.4 Cube 侧：直接消费，取消 GM 装载（✅ 实战验证）

```cpp
if (directL1_ == 1) {
    // 直读 l1Pool_（NZ 已就位），LoadNzL1ToZnL0B 正常工作
    uint64_t nzOff = slotBase
                   + (ki * BLOCK_N / C0) * C0 * dstNzC0Stride   // 列块 offset
                   + nL0Start * C0;                               // 行 offset
    // ⚠️ colC0Stride 必须用整块 NZ 的 dstNzC0Stride（如 topKBaseAlign16）
    LoadNzL1ToZnL0B(bL0, l1View_[nzOff], kAlign, nRowsAlign, dstNzC0Stride, false);
} else {
    auto tile = que_.AllocTensor<T>();
    LoadNdGmToNzL1(tile, wsGm_[off], ...);
    que_.EnQue(tile); tile = que_.DeQue<T>();
    LoadNzL1ToZnL0B(bL0, tile[0], kAlign, nRowsAlign, nRowsAlign, false);
    que_.FreeTensor(tile);
}
```

**直读 l1Pool_ 可以工作**（37/37 验证）。之前误判 LoadNzL1ToZnL0B 读 l1Pool_ 不对——实际是 vec 写法错（DataCopyParams NZ ≠ Nd2Nz NZ 或缺 V_MTE3 同步）导致的 mismatch，不是 LoadNzL1ToZnL0B 的问题。

**⚠️ colC0Stride 关键**：直通路径下 K_sel 在 l1Pool_ 是整块 NZ（dstNzC0Stride 如 topKBaseAlign16），colC0Stride 必须用整块值，不是小 NZ 的 nRowsAlign。

---

## 5. 最难的一环：NZ 布局契约

**这是本策略实施中最容易失败的部分。** 原两段式里，`GM→L1` 的 `Nd2Nz` 同时完成了「搬运 + 格式转换」；改成直通后，**格式转换的责任转移到了 Vector 侧**，而两侧对 NZ 的组织方式必须严格一致。

### 5.1 NZ 偏移公式

```text
元素偏移(r, c) = (c / C0) * C0 * C0Stride + r * C0 + (c % C0)
其中 C0 = 32B / sizeof(T)（fp16/bf16 为 16）
```

关键点：
- **行偏移是 `r * C0`，不是 `r`**（易错点 1）
- `dstNzC0Stride` 的**单位是 C0_SIZE（32B / DataBlock）**，不是元素数
  （fp16 下 C0=16 元素=32B，行数恰好等于 DataBlock 数，故传"行数"看似正确——但这是巧合，其它 dtype 会错）

### 5.2 两种 L1 组织方式，必须二选一并保持两侧一致

| 组织方式 | C0Stride | K-tile 偏移 | 适用 |
|---|---|---|---|
| **A. 多个独立小块**（每 tile 一个小 NZ 矩阵，紧密排列） | tile 自身行数（16 对齐） | `k * baseK * C0` | Cube 侧 **N 维不切**时 |
| **B. 一个大矩阵**（整槽一个 NZ 矩阵，Cube 切片消费） | 整槽行数 | `(c/C0)*C0*C0Stride` | Cube 侧 **N 维要切**时 |

成熟参考实现（`ops-transformer`）用的是 **A**，因为其 MM1 注释明确 *"m,n 不切，k 切 128"*——N 方向不分块，故每个 K-tile 在 L1 中独立紧密排列，`MatmulK` 内部按 `L1Boffset = baseK << 4` 步进。

若你的 Cube **N 维要切**（如按 `BLOCK_N` 遍历 n-tile），则须用 **B**，两侧偏移公式都要按大矩阵推导。

> **⚠️ 不要混用**：Vector 按 A 写、Cube 按 B 读（或反之）会导致 fractal 错位，
> 表现为**精度全错但编译与运行都正常**（无 device error）。

### 5.3 双 AIV 分工时的额外注意

若 Vector 侧是双 AIV 各写一半行，两者的 `dstOff` 必须落在**同一 NZ 矩阵的正确行位置**上，
即 `dstOff = (rowStart + base) * C0`，而非按 ND 的 `(rowStart + base) * colsAlign`。

### 5.4 ⚠️ 若同一份数据被**多个不同切法**消费，直通可能根本不成立

原两段式里数据落在 GM，是 **ND 布局**；每个消费点各自 `Nd2Nz` 出自己要的 NZ 分块，
**互不干扰**。改直通后 L1 里只有**一份固定的 NZ**，所有消费点必须都能从它切出来。

本例中同一份 `K_sel` 被两处消费：

| 消费点 | 切法 | `dstNzC0Stride` |
|---|---|---|
| MM1（`Q@K_sel^T`） | 沿 topK 切 N，沿 dk 切 K | `AlignUp16(nRows)`，nRows 是 **N 分块**行数 |
| MM2（`P@V_sel`） | 沿 topK 切 K，沿 dv 切 N | `AlignUp16(kRows)`，kRows 是 **K 分块**行数 |

两者对同一份数据的**行方向分块含义不同**（一个是矩阵的 N，一个是矩阵的 K），
只有当**两边的行分块粒度与列分块粒度都相同**（本例恰好都按 `BLOCK_N=128`）
时，才能共用同一套 `(rowTile, colTile)` NZ 小块网格。

**动手前必须先确认这一点。** 若两个消费点的分块粒度不同，可选：

1. 只让其中一个消费点吃 L1，另一个仍走 GM（**收益减半，但可先验证链路**）；
2. 统一两处的分块粒度（改动量大）；
3. 放弃直通。

> 本例采用了路线 1 作为**最小验证实验**——目的是把「同步 pipe」与「NZ 布局」
> 两个变量分离：先只改 MM1，若通过则说明链路成立，再推广到 MM2。

---

## 6. 已知陷阱

### AP-001：两侧各自 `InitBuffer`（最高频）

症状：`device error 507015`，**小 shape 可能通过、大 shape 挂**，极易误判为"容量不够"。
修复：§2.1，kernel 层统一分配 + 视图分发。

### AP-002：误用 `TSCM` 导致 L1→L0 断链

症状：`LoadData` 编译报错或行为异常（其只接受 `A1/B1/B2`）。
修复：§2.2，用 `TPosition::A1`。

### AP-003：忘开 `ENABLE_CV_COMM_VIA_SSBUF`

症状：**功能全对、精度全过，但性能毫无变化**（底层仍走 GM）。
修复：§2.4。验收时以 `mte2/mte3` 时间是否下降来反查。

### AP-003b：跨核 flag 的 wait pipe 未随路径改变

症状：精度全错、无 device error，**且最小 shape（无任何切片）也失败**。
辨别：先跑一个 `nTiles==1 && kTiles==1` 的用例——它若也错，就**不是**偏移问题。
修复：§2.3，AIC 侧 wait 从 `PIPE_MTE2` 改 `PIPE_MTE1`。

### AP-004：NZ 行偏移漏乘 C0

症状：精度全错，无 device error。
修复：§5.1，行偏移是 `r * C0`。

### AP-005：Vector 与 Cube 的 NZ 组织方式不一致

症状：精度全错，无 device error；**且看起来两边公式各自都"自洽"**。
修复：§5.2，明确选定 A 或 B，两侧按同一套推导。

### AP-006：L1 只分配一个 slot

症状：ring 流水下数据被后续 task 覆写，精度随机错。
修复：§4.2，按 `RING_SLOTS` 分配。

### AP-007：对切片视图误调 `FreeTensor`

症状：队列缓冲计数被破坏，后续 `AllocTensor` 行为异常。
修复：§4.4，直通路径不 Free。

### AP-008：把 `507015` 一律当设备故障

症状：反复换卡排查，浪费大量时间。
辨别方法：**在同一张卡上先跑基线**——基线过、改动挂 ⇒ 是代码问题；基线也挂 ⇒ 才是卡问题。
（实测遇到过卡 4 基线就挂、卡 5 基线正常的情况，不做对照必然误判。）

---

## 7. 实施历程与经验教训（✅ 已收敛，37/37 通过 2026-08-13）

**已确证可用：**

| 项 | 验证方式 | 结果 |
|---|---|---|
| UB→L1 搬运本身 | 小尺寸 buffer + 真实用例 | ✅ 37/37 |
| 跨核可见（AIV 写 / AIC 读同一 L1） | kernel 层统一分配 + 两侧视图 | ✅ 37/37 |
| 两侧各自 `InitBuffer` 会冲突 | 对照实验 | ✅ 已确证（AP-001） |
| L1 容量判定（GQA 够 / MLA 不够） | 逐 shape 核算 | ✅ 预算表见 §4.2 |

**✅ 已收敛（2026-08-13）：37/37 精度通过。** 最终三步式写法（Copy + V_MTE3 + DataCopyParams + MTE3_V）+ LoadNzL1ToZnL0B 直读 l1Pool_ 打通全链路。以下探针记录是迭代过程中的经验教训，保留供其他算子参考。

### 7.1 探针阶梯（每一步只动一个变量）

基线 = 37/37 通过。以下都是「仅 MM1 吃 L1、MM2 仍走 GM」的最小实验：

| 探针 | 改动（相对上一步只动一个变量） | 结果 | 排除了什么 |
|---|---|---|---|
| D2 | AIC wait 改 `PIPE_MTE1`；vec 额外写一份到 L1 | 7 failed / 30 passed | 从「37 全失败」大幅收敛 ⇒ 同步 pipe 方向正确 |
| D2a | 目的地仍是共享 L1，但数据**改回从 GM 装** | **1 failed（0.01% flaky）/ 36 passed** | ⇒ 共享 L1 分配、地址、同步**都是对的** |
| D2b | 直通态强制**单 AIV** gather | 8 failed | ⇒ **不是**双 AIV 行偏移问题 |
| D2d | vec 的 set flag 由 `PIPE_MTE3` 改 `PIPE_MTE2` | 7 failed（与 D2 相同） | ⇒ **不是** set flag 的 pipe 问题 |
| D2f | **cube 完全不读 L1**（走原 GM 路径），vec 仍写 L1 | **3 failed** | ⇒ vec 的 L1 写**破坏了别处**，不只是自己读错 |
| D2g | **vec 也完全不写 L1**，只保留 kernel 层那次 `InitBuffer` | **8 failed** | ⇒ 病因不是写入，是**分配动作本身** |
| D2h | 分配量 96KB → **1KB** | **7 failed**（与 D2g 相同） | ⇒ **不是容量挤占** |

**结论：病因是「在 AIV 上多做一次 `pipe->InitBuffer(TBuf<A1>)`」这个动作本身**——
它扰动了 `TPipe` 的隐式 event ID 分配，破坏了 vec 侧既有的 `SetFlag`/`WaitFlag` 配对。
详见 §2.0。该结论来自「仅 MM1 吃 L1、MM2 仍走 GM」的探针基线，不能直接外推到最终合入形态；最终合入的是 §2.0 的 kernel 层统一 `InitBuffer<TBuf<A1>>` + 视图分发（37/37 通过），BufferManager（§2.1）是另一种成熟写法，并非唯一解法。

顺带被这组探针**否证**的三个先前假设：
- ~~NZ 切片偏移公式写错~~（D2a 证明布局链路本身是通的）
- ~~双 AIV 行偏移~~（D2b）
- ~~set flag 的 pipe 不对~~（D2d）

而 §2.3 的「AIC wait 必须改 `PIPE_MTE1`」是**成立且必要**的（D2 的大幅收敛 + D2a 的 36/37）。

### 7.2 方法论教训（比结论更重要）

**教训一：探针本身不能引入新的 TPipe 资源。**
D2c 曾想加 `SetWaitFlag<MTE2_MTE3>` / `<V_MTE3>` 来 drain 所有 pipe，
结果连**退化路径**的用例都挂了——因为探针自己新增了 event，成了新变量。
**探针必须是零资源增量的**，否则测的是探针不是假设。

**教训二：「全部失败 + 耗时极短」是卡故障的特征，必须换卡复测再下结论。**
本轮有 3 次「37 全失败」，其中 2 次换卡后变成 7 failed / 30 passed——是卡在中途掉线。
纪律：**每轮测试前扫一遍卡；出现「全挂」先换卡复测，确认后再解读为代码问题。**

**教训三：当一个公式改两次仍不通过，就去构造能让它退化为恒等的用例。**
最小用例（`nTiles==1 && kTiles==1`，所有偏移恒为 0）也失败 ⇒ 一次性排除整个「偏移」方向。
这个对照只要 2 分钟，却比连续改三次公式有效得多。

**教训四：二分要沿「谁做了什么」而不是「哪里算错了」。**
D2f（cube 不读）→ D2g（vec 不写）→ D2h（只改大小）这条链，
把问题从「读得对不对」一路推到「分配这个动作有没有副作用」，
而这是任何数值推导都到不了的地方。

### 7.3 当前状态

代码**已合入直通改动并验证 37/37 通过**（dkAlign==128 场景全通；dk=576 MLA 退化两段式，待 Copy 分段支持）。
后续若要继续，起点是 §2.0 的 kernel 层统一分配 + 视图分发（或 §2.1 的 BufferManager 整块分配 + offset 切分重构），而非继续调偏移或同步。

> **卡故障与代码故障的辨别**（AP-008 的具体形态）：
> `TsdOpen failed. devId=N` / `open device 0 failed, runtime result = 507033`
> 出现在 **PyTorch `LazySetDevice` 阶段**，即 kernel 根本没被下发——
> 这一定是环境问题，与算子代码无关。看到它就停手等卡，不要继续改代码。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 平台 | 是否 arch35（950PR/950DT）？旧红线是否为 220x 遗留 |
| 数据流 | 哪段 `UB→GM→L1`；该数据是否仅用于核间传递 |
| L1 预算 | Cube 侧现有各 buffer 占用；新增 `RING_SLOTS × rows × colsAlign × dtypeSize`；**逐 shape** 核算 |
| 分配方式 | 是否由 kernel 层**一处**分配并分发视图 |
| TPosition | 是否用 `A1`（而非 TSCM） |
| **同步 pipe** | AIC 侧 wait 是否已从 `PIPE_MTE2` 改为 `PIPE_MTE1`（§2.3）；同 task 内若还有 GM 装载，是否补 `MTE1_MTE2` |
| 编译选项 | `ENABLE_CV_COMM_VIA_SSBUF` 如何注入；如何验证其生效 |
| **NZ 组织方式** | 选 A（多小块）还是 B（大矩阵）？Cube 的 N 维是否切分？两侧偏移公式分别是什么 |
| **消费者是否唯一** | 同一份 L1 数据是否被**多个不同切法**消费（如 MM1 按 n 切、MM2 按 k 切）？若是，两种切法的行/列分块粒度必须一致，否则一份 NZ 无法同时满足（见 §5.4） |
| 退化路径 | `directL1==0` 时是否完整保留原两段式 |
| 基线对照 | 同一张卡上的基线结果（用于区分卡故障与代码故障） |

任一项无法回答，不实施本策略。

---

## 9. 验收标准

```bash
bash <build> --soc=<soc> --op=<op> --wheel 2>&1 | grep -cE "error:"   # 须为 0
# 关键：同卡先跑基线，再跑改动
ASCEND_RT_VISIBLE_DEVICES=<d> pytest <op>/test/test_<op>.py -q        # 基线须全过
# 再跑改动版本
```

精度：**必须与基线完全一致**（本策略不改变任何数值语义，只改数据搬运路径）。

性能（profiling 归因）：

- Vector 侧 `mte3_time` 下降（少一次 GM 写）
- Cube 侧 `mte2_time` 下降（少一次 GM 读）
- workspace 总量下降（该分区可回收）
- **若上述指标均无变化，首先怀疑 `ENABLE_CV_COMM_VIA_SSBUF` 未生效**（AP-003）

边界：`directL1` 开/关两条路径各测；容量恰在判定边界的 shape 各测；不同 dtype（C0 不同）各测。

结论须写清：

```text
本策略消除 CV 通信的 GM 中转往返，省一次 GM 写 + 一次 GM 读 + workspace 容量。
仅 arch35(A5) 支持；旧算子里"禁 UB→L1"的红线多为 220x 遗留，移植时应复查。
三条硬约束：L1 一处统一分配 / 用 A1 而非 TSCM / 必须开 ENABLE_CV_COMM_VIA_SSBUF。
最难的是 NZ 布局契约——Vector 与 Cube 必须用同一套组织方式（多小块 or 大矩阵），
不一致会导致"编译运行都正常但精度全错"。偏移推导失败两次后应改用 DumpTensor 比对。
```

## 检索卡（短卡）

动作：将Vector侧中间数据由UB经GM中转到L1，改为UB→L1直通，消除GM往返。
适用：Ascend 950PR/950DT（arch35）上，Vector产出中间数据并由Cube消费。
限制：L1容量须按ring slot数分配；原workspace有多少轮转槽，L1须保留同样槽数。
范围：CV算子中Vector产出、Cube矩阵乘消费的中间数据通路。
检索词：Cube-Vector协同、UB→L1、TSCM、MTE3、MTE2、GM workspace。
机会：CV数据流仍包含UB→GM、跨核flag及GM→L1两段搬运。
