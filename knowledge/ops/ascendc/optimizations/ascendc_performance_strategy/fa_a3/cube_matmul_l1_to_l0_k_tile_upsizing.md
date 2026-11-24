---
type: Optimization
title: Cube 手写 Matmul 的 L1→L0 K 维单搬块放大
description: 在手工LoadData+Mmad矩阵乘中，将K内层切片步长由C0放大为K_L0_TILE。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/01-cube-matmul-l1-to-l0-k-tile-upsizing.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Cube 手写 Matmul 的 L1→L0 K 维单搬块放大

> **单一优化点：** 在任何由手工 `LoadData`(L1→L0) + `Mmad` 驱动的 AscendC Cube 矩阵乘中，把 K 归约维的内层切片步长从**最小分形宽度 `C0`** 放大到 `K_L0_TILE`（`C0` 的整数倍）。一次 `LoadData` 搬运更多 K 列、一次 `Mmad` 归约更多 K，从而提升 L0A/L0B 空间利用率、降低 `LoadData`/`Mmad` 指令数及其附带的 Cube scalar 地址/循环开销。
>
> **算子无关性：** 本策略适用于**所有**"K 维被 `C0` 细切"的手写 Cube matmul，不限于任何具体算子；只要存在形如 `for ki in K step C0: LoadData; LoadData; Mmad(k=C0)` 的内层循环即可套用。
>
> **整体收益是条件性的：** 本策略只降低 Cube 侧工作量；若算子同时被 Vector 侧共瓶颈锁住，整体时长可能持平——判定成功与否须看 Cube 侧指标（见 §10）。

本策略只改"K 维内层单搬块大小"。GM→L1 装载、L1 布局、M/N 维 tiling、L0A/L0B/L0C 缓冲深度、TQue 双缓冲、跨核同步、Vector 侧、软流水、搬运-计算重叠均不是本策略范围。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

手写 Cube matmul 的典型低效基线把 K 维按分形宽度 `C0` 切：

```text
for mBlock in M:            # 左矩阵行块
  for nBlock in N:          # 右矩阵行/列块（含可能的 KV 外层块）
    for ki in K step C0:    # <-- 问题：K 按 C0 切
      LoadData L1 -> L0A : left[m, C0]
      LoadData L1 -> L0B : right[C0, n]   # 或转置语义
      Mmad(cL0, aL0, bL0, k = C0)
```

`C0 = 32B / sizeof(T)`（fp16/bf16=16，int8=32）。每个 `C0`-tile 产生一条 `LoadData`+一条 `Mmad`，并附带：

- **L0A/L0B 利用率低**：单缓冲 32KB，当 M/N 行块对齐量较大时，一个 `C0` 列块只占单 tile 容量的 `1/(M_align/C0)` 左右（fp16、`M_align=64` 时仅约 6%）。
- **Cube scalar 开销放大**：每个 tile 的 `AllocTensor/EnQue/DeQue/FreeTensor`、`MmadParams` 构造、地址计算、`PipeBarrier` 都走 Cube scalar 单元。tile 数 = `K/C0`，scalar 时间随 K 线性堆叠。

典型症状：profiling 显示 `aic_scalar_time` 占 `aicore_time` 比例显著，远高于 `aic_mac`（算力）与 `aic_mte1`（搬运）——Cube 受限于**指令/循环开销**而非算力或带宽。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| L0A/L0B 片上容量 | 单缓冲足以容纳 `M_align × K_L0_TILE` / `K_L0_TILE × X_align` 大块，利用率从个位数升到 50%~100% |
| LoadData3D/2D 参数 | `channelSize`（3D）/`repeatTimes`（2D）天然支持一次搬运 `C0` 整数倍列，**不增加**指令条数内的搬运总量 |
| Cube scalar 单元 | tile 数 `K/C0` → `ceil(K/K_L0_TILE)`，每 tile scalar/地址开销随之下降 |
| 计算流水 / 核间协作 | 沿用既有 TQue 双缓冲与跨核 flag，不改变流水与协议 |

核心改动只是内层步长与 `LoadData`/`Mmad` 的 K 入参：

```text
for ki in K step K_L0_TILE:           # 一次搬 K_L0_TILE 列
  kTile = min(K_L0_TILE, K - kOff)    # K 维尾块
  LoadData L1 -> L0A : left[m, kTile]
  LoadData L1 -> L0B : right[kTile, n]
  Mmad(cL0, aL0, bL0, k = kTile)
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 计算形态 | Cube 侧存在手工 `LoadData`+`Mmad` 驱动的矩阵乘（含 `QK^T`、`PV`、任意 GEMM/GEMV）；**不适用**于 Matmul 高阶 API（其 K 切分由 `TCubeTiling` 控制，不在 kernel 内手写） |
| 当前 K 切片 | 基线内层 K 步长恰为 `C0` |
| 分形对齐 | `K_L0_TILE % C0 == 0`；每个 tile 的 `kTile` 也为 `C0` 倍数（K 维尾块需 `min` 后仍为 C0 倍数，否则依赖"覆盖最右分形"例外） |
| L0A 容量 | `(M 侧对齐量) × K_L0_TILE × sizeof(T) ≤ L0A 单缓冲` |
| L0B 容量 | `K_L0_TILE × (与 K 共享 L0B 的另一操作数对齐量) × sizeof(T) ≤ L0B 单缓冲` |
| LoadData 参数界 | 所用搬运路径的 `channelSize`（3D）/`repeatTimes`（2D）不得超过已验证上限（见 §6.1） |
| L1 源连续性 | 一次大块 `LoadData` 覆盖的多个 `C0` 列块/行块在 L1 源布局中**物理连续**（见 §4.3） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- K 维较大（`K/C0 ≥ 16` 量级），tile 数显著。
- profiling 显示 `aic_scalar` 或 `aic_mte1` 占 `aicore_time` 比例高（scalar/搬运指令受限）。
- L0A/L0B 单 tile 利用率低（`M_align × C0` 或 `C0 × X_align` 远小于单缓冲）。

不适用或需先重构：

- K 维本身就是 `C0` 量级，放大无空间。
- L0A/L0B 已被 M/N 维占满，无 K 放大余量（需先缩 M/N 或改 buffer 深度，属另一策略）。
- 矩阵乘走 Matmul 高阶 API（改 `TCubeTiling.baseM/baseN/baseK`，不走本策略）。
- L1 源多段 K 不连续且无法证明连续性（见 §4.3）。
- 目标收益来自 GM→L1、Vector 侧、软流水或 double buffer——非本策略。
- 整体瓶颈在 Vector 侧、Cube 已非关键路径——本策略只降 Cube 工作量，**不保证**整体提速（见 §10）。

---

## 3. K_L0_TILE 选择规则

`K_L0_TILE` 通常作为 kernel 内常量即可；若需按 shape 自适应，可在 `TilingData` 增加 `kL0Tile` 字段。记号：

```text
C0       = 32B / sizeof(T)                 # 分形次维宽度
L0A_elem = L0A_SINGLE_BYTES / sizeof(T)    # 910B = 32768/sizeof(T)
L0B_elem = L0B_SINGLE_BYTES / sizeof(T)    # 910B = 32768/sizeof(T)
M_align  = AlignUp(M_per_tile, C0)         # L0A 中左矩阵 M 侧对齐量
X_align  = L0B 中与 K 并列的另一操作数对齐量
           - 对 QK^T(右矩阵转置): X_align = kvRowsAlign (N 侧)
           - 对 PV / 普通 GEMM:    X_align = nAlign (N 侧)
```

选择函数：

```text
SelectKL0Tile(M_align, X_align):
  capA = floor(L0A_elem / M_align)        # L0A 约束
  capB = floor(L0B_elem / X_align)        # L0B 约束
  capC = channelSizeCap                   # 见 §6.1，逐路径验证
  k0   = min(capA, capB, capC)
  K_L0_TILE = floor_to_multiple_of_C0(k0)
  # 可选：优先选能整除 K 的值以减少/消除尾块；不能整除则靠 §6.3 尾块处理兜底
  return K_L0_TILE
```

**取值取舍（通用）：**

- 在 `min(capA,capB,capC)` 内尽量取大以最大化利用率与 tile 数下降；但**精确满配单缓冲**（`M_align×K_L0_TILE == L0A_elem` 等）无余量，若该搬运路径的 `channelSize`/分形未独立验证，优先降一档留余量。
- 优先整除 K 的值可消除尾块分支；不能整除时尾块用 §6.3 兜底，仍安全。

---

## 4. 数据与缓存布局

### 4.1 L0A/L0B 单 tile 形状与容量

L0A 为 ZZ 分形，L0B 为 ZN 分形，次维 `C0`。一次大块 `LoadData` 产出整数个分形；当各维均为 `C0` 倍数时无 padding。

| 缓存 | 单 tile 逻辑形状 | 容量约束 |
|---|---|---|
| L0A（左矩阵） | `[M_align, K_L0_TILE]` | `M_align × K_L0_TILE ≤ L0A_elem` |
| L0B（右矩阵） | `[K_L0_TILE, X_align]` | `K_L0_TILE × X_align ≤ L0B_elem` |
| L0C（累加器） | `[M_align, N_align]` | 不受 K 块影响（K 是归约维，不进 L0C 维度） |

### 4.2 容量核算（通用模板）

```text
L0A tile 字节 = M_align * K_L0_TILE * sizeof(T)   ≤ L0A 单缓冲
L0B tile 字节 = K_L0_TILE * X_align * sizeof(T)   ≤ L0B 单缓冲
(双缓冲下两 tile 并存，总量 ≤ 硬件 L0A/L0B 总容量)
```

放大 `K_L0_TILE` 或 M/N 维时必须重算；尤其 `K_L0_TILE × X_align` 易触顶（X_align 较大时，如 N 侧 = 256）。

### 4.3 L1 源连续性契约（正确性关键，逐算子证明）

放大 K 块要求"一次 `LoadData` 覆盖的多个 `C0` 列块/行块在 L1 源布局中物理连续"。**不可假设**，必须逐段证明：

- 若 L1 源是单段连续 NZ/ND tile（如 `K[dim]`、`V[kvRows, dim]`），其 `C0` 列块/行块天然连续 → 可直接放大。
- 若 K 由多段拼接（如同一 head dim 内两段语义不同的子段拼接、或多 head 拼接），必须证明段间**无 padding、无 stride 间隔**；连续则可统一寻址放大，不连续则**分段各自放大**或先修 L1 装载布局。

---

## 5. 实施步骤

### 5.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| Cube kernel 内 MM 函数 | 新增 `K_L0_TILE` 常量；内层 K 循环步长 `C0 → K_L0_TILE`；`LoadData` 的 K 入参 `C0 → kTile`；`Mmad` 的 `k` 入参 `C0 → kTile` |
| L1→L0 helper（若有） | **通常不改**；多数 `LoadData3D`/`LoadData2D` helper 天然支持 `k>C0`（见 §6.1）。仅当 helper 内部写死 `C0` 时才需泛化其参数 |
| Tiling / Host / Vector / Kernel 顶层调度 | **不改** |

### 5.2 helper capability inventory（实施前必做）

helper 名是当前仓库候选，不是跨算子稳定 API。实施前按 **capability**（而非名称）确认定义与语义：

| capability | 数学阶段 | 源 L1 布局 → 目标 L0 语义 | k>C0 成立条件 |
|---|---|---|---|
| `l1_to_l0a_left` | 任一 MM 左矩阵 | L1 NZ `[M, K]` → L0A ZZ `[M, K]` | `LoadData3D` 的 `channelSize/mExtension/kExtension` 随 K 线性放大；见 §6.1 证明 |
| `l1_to_l0b_transposed` | `QK^T` 类（右矩阵需转置） | L1 NZ `R[N, K]` → L0B ZN `[K, N]` | `LoadData2D` 的 `repeatTimes=(k/c0)*(n/c0)` 随 K 放大；或 `LoadData3D` 转置路径 |
| `l1_to_l0b_regular` | `PV` / 普通 GEMM 右矩阵 | L1 NZ `R[K, N]` → L0B ZN `[K, N]` | `LoadData3D` `mExtension=K` 放大；`channelSize=N` 不变 |
| `l0c_to_gm` | Fixpipe | L0C → GM/workspace | K 是归约维，不影响 |

**红线**：转置右矩阵 capability（`QK^T`）与普通右矩阵 capability（`PV`）不同；普通右矩阵 helper 成功**不构成**转置 helper 可用的证据。helper 不存在或语义不符时，用显式 `LoadData2DParams`/`LoadData3DParamsV2` fallback，写清 `repeatTimes/srcStride/channelSize/mExtension` 与 `C0` 分块关系。

### 5.3 通用内层 K 循环改写

```text
# 基线
for ki in 0 .. K step C0:
    left_l0  = LoadData L1 -> L0A, k = C0
    right_l0 = LoadData L1 -> L0B, k = C0   # 转置或普通视阶段
    Mmad(cL0, left_l0, right_l0, k = C0, cmatrixInitVal = (ki == 0))

# 改写后
kTiles = CeilDiv(K, K_L0_TILE)
for ki in 0 .. kTiles:
    kOff  = ki * K_L0_TILE
    kTile = MinU32(K_L0_TILE, K - kOff)            # K 维尾块
    left_l0  = LoadData L1 -> L0A, k = kTile, srcOff = kOff * M_align
    right_l0 = LoadData L1 -> L0B, k = kTile, srcOff = <按布局导出>
    Mmad(cL0, left_l0, right_l0, k = kTile,
         cmatrixInitVal = (ki == 0))
    if ki > 0: PipeBarrier<PIPE_M>()               # 续接累加前等上一 Mmad 写完
```

源偏移 `srcOff` 按 L1 布局导出：

- 左矩阵 NZ `[M_align, K]`（`dstNzC0Stride=M_align`）：列块连续，`kOff` 列起偏移 = `kOff * M_align`。
- 右矩阵（普通）NZ `[K_align, N]`：K 行块在列块内连续，`kOff` 行起偏移按 `列块偏移 + kOff*C0` 类形式导出（具体随 `dstNzC0Stride`）。
- 多段连续 K：统一寻址自动跨段（段起始恰为前段尾）。

`cL0` 在整个 K 循环内单次分配、跨 tile 累加；`cmatrixInitVal` 仅首 tile 真。

---

## 6. 正确性红线

### 6.1 LoadData 对 k>C0 的成立性证明（通用）

- **`LoadData3D`（`channelSize=K`）**：以常见 L1(NZ)→L0A(ZZ) 的 `l1H=1, l1W=M, channelSize=K` 惯用法为例，源 NZ 单列块 `[M/C0][C0][C0]` 线性地址 `(mb*C0+r)*C0+c = row*C0+col`（`mb*C0+r=row`），与 `[M][C0]`（`w=row, ch=c`）**完全同构**。故 `channelSize=K`（C0 倍数）读取 `K/C0` 个连续列块，img2col 仍产出 ZZ `[M, K]`。推广：只要 `M`、`K` 为 `C0` 倍数（或覆盖最右/最下分形例外），`LoadData3D` 对任意 `k=C0·整数` 成立。
- **`LoadData2D`**：`repeatTimes = (k/c0)*(n/c0)`，每 repeat 搬一个 `C0×C0` 分形，`srcStride=1` 连续；`k` 放大仅放大 `repeatTimes`。
- **`channelSize` 实际上限**：官方文档 `channelSize∈[1,63]` 为过时区间，字段实为 `uint16_t`，实测可支持远大于 63 的取值。超出既有验证范围的取值需独立验证后再用。

### 6.2 同步与生命周期

- L0A/L0B 沿用原 TQue 双缓冲（`AllocTensor/EnQue/DeQue/FreeTensor`），同步语义不变。
- tile 间 `PipeBarrier<PIPE_M>()` 保证上一 `Mmad` 的 L0C 写完成后再累加（仅首 tile `cmatrixInitVal=true` 可跳过）。
- 不删除任何跨核 flag、queue acquire/release 或 L1 生命周期同步；不与"删同步""改 buffer 深度"混在同一实验。

### 6.3 边界处理

- K 维尾块：`kTiles = CeilDiv(K, K_L0_TILE)`，`kTile = MinU32(K_L0_TILE, K - kOff)`；**必须 ceil**，禁止 floor 除法（见 §7 陷阱 1）。
- 尾块 `kTile` 须为 `C0` 倍数；若 `K % C0 != 0`，依赖"覆盖最右分形"例外或先对齐 K。
- M/N 维尾块、输出 clamp 沿用基线，不在本策略修改。

### 6.4 数值正确性

- 不改变 scale、mask、累加顺序语义、输出 dtype/布局。K 归约加法结合顺序因 tile 变大而变，浮点结果允许 ≤atol 的微小差异。
- `cmatrixInitVal` 仅首 tile 真，等价于"首块初始化 L0C、其余续接"。

---

## 7. 已知陷阱

### 陷阱 1：tile 数用 floor 除法漏算 K 维尾块

问题：`kTiles = K / K_L0_TILE`（floor）写成定式。
触发：`K` 非 `K_L0_TILE` 倍数，或子块（如 attention 的内层 KV chunk）`K_sub < K_L0_TILE`。
症状：`kTiles=0` 或偏小，内层 K 循环少算尾段，该 `(m,n)` 结果错误/全零，mismatch 大面积。
修复：`kTiles = CeilDiv(K, K_L0_TILE)`，`kTile = MinU32(K_L0_TILE, K - kOff)`。

### 陷阱 2：多段 K 非连续时强行统一寻址

问题：假设多段 K（如多段子段拼接、多 head）在 L1 连续，实际有 padding/不同 stride。
症状：后段读错地址，mismatch 集中在对应输出维度。
修复：实施前逐段证明连续性（§4.3）；不连续则分段各自放大，仅段内放大大块。

### 陷阱 3：L0B 因 `K_L0_TILE × X_align` 触顶

问题：放大 `K_L0_TILE` 而 X_align（N 侧等）未降，`K_L0_TILE × X_align` 超单缓冲。
症状：buffer 越界 / 编译期校验失败 / 数据踩踏。
修复：`K_L0_TILE ≤ L0B_elem / X_align`；要放大 K 须同步缩 X_align（属 N/M 维 tiling 策略）。

### 陷阱 4：只凭 helper 名称跨算子迁移

问题：把普通右矩阵 helper 当转置右矩阵 helper，或假设所有算子有同名 helper。
症状：转置阶段数值错误或编译失败。
修复：先做 §5.2 capability inventory；语义不符用显式 primitive fallback。

### 陷阱 5：误判整体未提速为策略失效

问题：本策略使 Cube 工作量下降，但整体 `Task Duration` 持平，误以为没生效而回退。
诊断：看 `aic_mte1/aic_scalar/aic_mac` 是否下降。下降而整体持平 = 瓶颈转移到 Vector 侧，本策略对 Cube 已生效（见 §10）。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 计算形态 | 是否手写 `LoadData`+`Mmad`（非 Matmul 高阶 API）？存在几个 MM 阶段 |
| 当前 K 切片 | 内层 K 步长是否为 `C0`？各阶段 `K`（及子块 `K_sub`）取值 |
| 目标 shape / dtype | 决定 `C0`、`L0A_elem/L0B_elem` |
| L0 容量 | `L0A/L0B 单缓冲`、各阶段 `M_align`、`X_align` |
| K_L0_TILE 选择 | 各阶段取值与四类约束（C0 倍数、L0A、L0B、channelSize）核算 |
| L1 连续性 | 多段 K 是否物理连续（给出偏移证明） |
| helper capability | 各阶段左/右矩阵用哪个 capability 或 fallback，k>C0 成立性 |
| 尾块处理 | `CeilDiv`/`MinU32` 落点；`K % C0 != 0` 如何兜底 |
| 瓶颈定位 | profiling `aic_scalar/mte1/mac` 与 `aiv_*` 占比；Cube 是否关键路径 |
| 同步保护 | tile 间 `PipeBarrier`、`cmatrixInitVal`、TQue 双缓冲是否保持基线语义 |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 同一轮混入 GM→L1 装载改动、M/N tiling 改动、buffer 深度调整、同步删减、软流水、Vector 侧改动或新 helper。
- 改变数学公式、scale、mask、累加顺序、输出布局或 dtype。
- 用 floor 除法算 `kTiles`（§7 陷阱 1）。
- 未证明 L1 连续性时统一多段 K 寻址（§7 陷阱 2）。
- 让 `K_L0_TILE × X_align` 或 `M_align × K_L0_TILE` 超单缓冲（§7 陷阱 3）。
- 只凭 helper 名称跨算子迁移（§7 陷阱 4）。
- 因某 shape 通过就跳过 K 维尾块、小子块与多 `(m,n)` 组合测试。

回退或缩小策略的条件：

- L0A/L0B 容量核算超限。
- 精度失败且无法定位到尾块（§7 陷阱 1）/连续性（§7 陷阱 2）/helper 语义（§7 陷阱 4）单一原因。
- 编译失败来自 `channelSize`/`repeatTimes` 与 `C0` 分块不一致。
- profiling 显示 `aic_mte1`/`aic_scalar` **未下降**——改动未生效或 K 切分非瓶颈，重新归因（区别于 §7 陷阱 5 的"下降但整体持平"）。
- 需依赖未验证的 `channelSize` 超限才能编过；改用更小 `K_L0_TILE` 或拆分。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>            # 编译算子
bash <build> --soc=<soc> --op=<op> --wheel    # 编译 pta
source <set_env>                              # source custom 包
pytest <op>/test/test_<op>_*.py               # 精度 + 性能（生成 profiling）
```

精度：与基线一致（沿用算子既有 `atol/rtol`）。K 归约顺序变化允许 ≤atol 微小差异。

性能（**必须用 profiling 归因，不能只看整体 µs**）：

- Cube 侧 `aic_mte1_time`、`aic_scalar_time`、`aic_mac_time` 相对基线明显下降。
- 整体 `Task Duration` 不劣化。
- **整体提速是条件性的**：仅当 Cube 是关键路径（修改前 `aicore_time` 显著大于 `aiv_time`，或 Cube scalar/mac 占比显著高于 Vector）时本策略才带来整体 µs 下降。若修改前 `aiv_time ≈ aicore_time` 且 Vector `aiv_scalar/aiv_mte2` 占比高，本策略降 Cube 后整体会**持平**（瓶颈转移到 Vector）——此时策略对 Cube 判定成功，整体提速需叠加 Vector 侧独立策略。

边界 shape：K 维非 `K_L0_TILE` 倍数（尾块）、小子块 `K_sub < K_L0_TILE`、M/N 尾块、不同 dtype（影响 `C0`）。

性能结论必须写清基线与归因：

```text
本策略收益相对"C0 单搬块"基线；判据是 Cube aic_mte1/scalar/mac 下降，而非整体 µs。
整体持平若因 Vector 共瓶颈，后续 Vector 策略须相对"本策略后"评估，
不能回到 C0 基线作增量起点，也不能把整体持平误判为本策略失效。
```

## 检索卡（短卡）

动作：在手工LoadData+Mmad矩阵乘中，将K内层切片步长由C0放大为K_L0_TILE。
适用：Cube侧矩阵乘由手工LoadData与Mmad驱动。
限制：L0A/L0B单缓冲必须容纳放大的矩阵块，并逐算子证明L1源数据连续性。
范围：AscendC Cube手写矩阵乘的L1→L0 K内层循环。
检索词：Cube Matmul、LoadData、Mmad、L1→L0、L0A/L0B、K_L0_TILE、C0、K归约维
机会：手写Cube矩阵乘仍按分形宽度C0切分K归约维。
