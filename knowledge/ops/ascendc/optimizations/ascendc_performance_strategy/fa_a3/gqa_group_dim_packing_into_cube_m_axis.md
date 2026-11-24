---
type: Optimization
title: GQA/MQA group 维打包进 Cube M 轴（共享 KV 摊销 + M 满载）
description: 由每个query head独立任务改为将group维打包进Cube M轴，mBaseSize取G或min(G,BLOCK_M)
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/01-gqa-group-dim-packing-into-cube-m-axis.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：GQA/MQA group 维打包进 Cube M 轴（共享 KV 摊销 + M 满载）

> **单一优化点：** 在分组查询注意力（GQA/MQA，`G = N_q / N_kv ≥ 1` 个 query head 共享同一组 KV）的 Cube 矩阵乘中，把**共享同一 KV 的 G 个 query head 折叠进 Cube 的 M 轴**（`M = G`，或 `M = G × S` 与序列维合并），而不是"每个 query head 一个 tile"或"每个序列块一个 tile"。一次 `Q@K^T` / `P@V` 同时算 G 个 head，KV 在 L1 装载一次被 G 个 head 复用；同时把 decode 场景下 `M = min(BLOCK_M, S) = 1` 被 pad 到 `C0` 的 Cube 浪费消除（M 直接由 G 撑满）。
>
> **算子无关性：** 本策略适用于**所有** GQA/MQA 形态的注意力及其变体，只要"多个 query head 共享一组 KV"且 Cube 走手写 `LoadData`+`Mmad`（或 Matmul 高阶 API 的 M 轴 tiling 可控）。也推广到任意"一组输出共享同一右操作数"的批 GEMM 模式。
>
> **layout 边界：** head 在源布局中不连续且 head-stride 超出 `Nd2Nz srcDValue` 上限的 case（如 BNSD 长 prefill）不应强行打包，须退回"序列维进 M"的兜底路径，保证不劣化（见 §3）。

本策略只改"M 轴折叠哪个维度（group vs seq）"+ 与之联动的 task 模型/Q 载入/causal/写回寻址。不改变 L0A/L0B/L0C 结构、K 维切分、TQue 双缓冲、跨核同步、Vector softmax 数学、scale/mask 语义。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

GQA/MQA 注意力的默认 tiling 把"每个 query head"或"每个序列块"作为独立 task，Cube M 轴只承载序列维：

```text
for bz in B:
  for kvHead in N_kv:
    for groupId in G:        # <-- 问题：group 维做外层 task 切分
      for seqBlock in S:
        for kvPos in S_kv:
          Q = load Q[bz, seqBlock, kvHead*G+groupId, :]   # M = seqRows
          K = load K[bz, kvPos, kvHead, :]                   # 每个 group head 都重载同一 K
          V = load V[bz, kvPos, kvHead, :]                   # 每个 group head 都重载同一 V
          Mmad Q@K^T ; softmax ; Mmad P@V
```

两个叠加的低效：

- **Cube M 轴欠载（decode 致命）：** decode 场景 `S=1`，`M = min(BLOCK_M, S) = 1`，硬件把 M pad 到 `C0`（fp16=16）。一个 `C0×N×K` 的 Mmad 只产出 1 个有效行，Cube 算力浪费约 `C0×`（fp16 ≈16×）；同时 group 维被拆成 `G` 个独立 task，task 派发/跨核同步开销放大 `G×`。
- **KV 按 head 重复装载：** GQA 下 G 个 query head 共享同一组 `K/V`，但"group 维做外层 task"使每个 head 的 task 各自重载同一份 `K/V`，GM→L1 搬运量放大 `G×`。

典型症状：profiling 显示 decode 极慢，Cube `aic_mac` 利用率极低（M 被 pad），`aic_mte2`(GM→L1) 因 KV 重复装载而偏高。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| Cube Mmad M 轴容量 | 单 tile `BLOCK_M=128` 可容纳 `G` 个 head（`G ≤ 128` 时 M 直接由 G 撑满，不再 pad） |
| K/V L1 复用 | G 个 head 共享同一 `K/V`，折叠进 M 后 K/V 装载一次、被 M 内 G 行复用（搬运量 `/G`） |
| Nd2Nz 连续装载 | head 在源布局中相邻时（BSND），G 个 head 是物理连续块，单次 `Nd2Nz` 装载 |
| Cube scalar / task 派发 | task 数从 `(B·N_kv)·G·qOuter` 降到 `(B·N_kv)·sQ`（decode 省 ≈`G×`） |

核心改动：group 维从"外层 task"改为"M 轴行"，序列维退化为外层 task（每个 task = 1 个 seqPos × 整个 group）：

```text
for bz in B:
  for kvHead in N_kv:
    for seqPos in S:                  # group 已并入 M，外层只剩 seqPos
      for kvPos in S_kv:
        Q = load Q[bz, seqPos, kvHead*G : kvHead*G+G, :]   # M = G 个 head（连续）
        K = load K[bz, kvPos, kvHead, :]                       # 装载一次，G 行复用
        V = load V[bz, kvPos, kvHead, :]                       # 装载一次，G 行复用
        Mmad Q@K^T (M=G) ; softmax(行=group head) ; Mmad P@V (M=G)
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 注意力形态 | GQA/MQA：`G = N_q / N_kv ≥ 1` 整数；多个 query head 共享同一组 KV |
| Cube 形态 | 手写 `LoadData`+`Mmad`，或 Matmul 高阶 API 且 M 轴 tiling 可由 `TilingData` 控制 |
| group 规模 | `G ≤ BLOCK_M`（910B 典型 128）；`G > BLOCK_M` 时需分多个 M tile（仍可套用，见 §3） |
| Q head 连续性 | group 内 G 个 head 在 Q 源布局中**相邻且等距**，可用单次 `Nd2Nz`（head-stride ≤ `srcDValue` 上限）装载；否则逐 head 装载或退化为"序列维进 M"的兜底路径（见 §3） |
| softmax 行独立性 | softmax 沿 K 归约、对每行独立 → group head 进 M 行后逐行 softmax 语义不变（必须满足） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- decode / 小 `S`（`S < BLOCK_M`）：M 欠载最严重，收益最大。
- `G` 较大（接近 `BLOCK_M`）：M 一次撑满。
- KV 较大（长 `S_kv`、大 head dim）：KV 复用摊销显著。

不适用或需先重构：

- **MHA（`G=1`，`N_q == N_kv`）**：无 group 可打包，本策略退化为 no-op；此时 M 轴应承载序列维。
- head 在源布局中非连续且 head-stride 超 `Nd2Nz srcDValue` 上限（如 BNSD 长 prefill，`head-stride = S·d > 65535`）：强行 group-pack 会退化成逐 head strided gather，**整体劣化**——此时保留"序列维进 M"的兜底路径（layout 感知双路径，见 §3）。
- softmax 非行独立（如跨 head 共享归约因子的变体）：不能简单把 head 塞进 M 行。
- group 维打包后 L1 Q tile 超容量（`G · D_q · sizeof(T) > Q_L1 单缓冲`）：需先缩 D 或分 M tile。

---

## 3. group-packed M 的选择与 layout 分支

### 3.1 M 轴构成

```text
G = N_q / N_kv                              # group 头数
# 优先：M 轴 = 整个 group（每 task 1 个 seqPos）
mBaseSize = G                                # M = G（G ≤ BLOCK_M 时）
# 若 G > BLOCK_M：M = BLOCK_M，group 维拆 ceil(G/BLOCK_M) 个 M tile（每 tile 仍复用同一 KV）
```

序列维 `S` 退化为外层 task（`totalWork = (B·N_kv) · sQ`，每 task 处理 1 个 seqPos × 整个 group）。若 `G < BLOCK_M` 且 `S` 较大，可进一步把 `S` 也折进 M（`M = G · seqPerM`，gS 打包），但因果 mask 与写回寻址会随行变化（见 §6.2），复杂度上升；`G` 已填满 `BLOCK_M` 时不必。

### 3.2 layout 感知：何时 group-pack，何时退回序列维兜底

group-pack 要求 G 个 head 能高效装载。判据是 **head-stride**（源布局中相邻 head 的元素步长）：

```text
# BSND [B,S,N,d]：head 维是次末维，相邻 head 步长 = d        → 恒 ≤ 65535，可 group-pack
# BNSD [B,N,S,d]：head 维是次维，相邻 head 步长 = S·d       → S·d > 65535 时不可单次 Nd2Nz
headStride    = (layout == BSND) ? d : S·d
canGroupPack  = (headStride ≤ 65535)
```

- `canGroupPack = true`：M 轴 = group，单次 `Nd2Nz`（`srcDValue = headStride`）装载 G 个 head。
- `canGroupPack = false`（如 BNSD 长 prefill）：**保留"M 轴 = 序列维"的序列兜底路径**，Q 按序列行装载（此时序列行在 BNSD 中连续）。两条路径共存于同一 kernel（按判据分支），避免 strided gather 劣化。

> **为何不直接对 BNSD 长 prefill 也 group-pack + 逐 head 装载：** 逐 head `Nd2Nz`（per-head 一条 DMA）在长 prefill（`S` 大、task 多）下 DMA 条数爆炸，整体显著劣化。head-stride 超限时退回序列维兜底是**正确性等价、性能不劣化**的兜底（§7 陷阱 1）。

---

## 4. 数据与缓存布局

### 4.1 Q 切片（group-head 连续块）

group-pack 下 Q 切片 = 固定 `(bz, seqPos)` 下 G 个连续 head：

```text
qHeadBase = kvHead * G
qGmOff = OffsetQ(bz, qHeadBase, seqPos, d)               # group 首 head 起点
LoadNdGmToNzL1(qL1, Q[qGmOff], m=G, n=d, srcDValue=headStride, dstNzC0Stride=Q_L1_ROWS)
# 若 Q 在 head dim 上由多段拼接，后续段紧接前段之后（偏移 = d_seg * Q_L1_ROWS）
```

- BSND：head-stride = `d`，G 个 head 物理连续 → 单次 `Nd2Nz` 读 `[G × d]` 连续块。
- BNSD（可 group-pack 分支，仅小 `S`）：head-stride = `S·d`，`Nd2Nz srcDValue=S·d` 做跨步读取（仍单次）。

K/V 切片与基线一致（按 `(bz, kvHead, kvPos)` 装载），不随 group 维变化——这是 KV 被 G 行复用的关键。

### 4.2 score / P / 输出 矩阵的 M 维语义

| 矩阵 | 形状 | M 行语义 |
|---|---|---|
| score `S = Q@K^T` | `[G × S_kv]` | 行 = group head（`qHeadBase + row`） |
| `P = softmax(S)` | `[G × S_kv]` | 行 = group head（逐行 softmax，行独立） |
| `O = P@V` | `[G × d]` | 行 = group head |

L1/L0 缓冲容量按 `M = G` 重算：`Q_L1 ≥ G·D_qk·sizeof(T)`、`P_L1 ≥ G·S_kv·sizeof(T)`、`L0C ≥ G·N_align·sizeof(float)`。`G ≤ BLOCK_M` 时原有"按 BLOCK_M 预算"的缓冲天然够用。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| Host tiling | `mBaseSize = G`（或 `min(G, BLOCK_M)`）；`totalWork = (B·N_kv)·sQ`；`qOuterBlocks = sQ`（每 task 1 seqPos）；新增/派生可 group-pack 判据（head-stride ≤ 上限）传入 kernel |
| Kernel task 模型 | task 构造：`groupId` 从"外层 task 维"改为"M 轴行"；task = `(bz, kvHead, seqPos, kvPos)`，`qHeadBase = kvHead·G`，`groupRows = G`，`seqPos` 进 task 信息 |
| Cube `QK^T` Q 载入 | 按 §4.1 装载 G 个连续 head（`srcDValue = headStride`），Mmad `M = G` |
| Cube `P@V` | 形状不变（M=G），K/V 已天然复用 |
| Vec `softmax` | 逐行（行=group head），结构不变 |
| Vec causal mask | 同一 task 内所有 M 行同一 `seqPos` → mask 阈值**对所有行一致**（见 §6.2） |
| Vec 输出写回 | 行 `i` → `y[bz, seqPos, qHeadBase+i, :]`（head 维寻址，见 §6.3） |

### 5.2 layout 感知双路径

`canGroupPack`（或等效判据）在 host 与 kernel 用**同一公式**计算（§3.2），保证一致。kernel 内 task 构造 / Q 载入 / causal / 写回四处按该判据分支：true 走 group-pack，false 走序列维兜底（M=序列维，causal 随行变化，写回按序列行）。

### 5.3 通用 task 解码改写

```text
# 基线（group 维做外层 task）
groupId = taskId / qOuterBlocks
qHead   = kvHead * G + groupId
qRows   = seqRows                                          # M = 序列维

# group-pack（group 维进 M）
seqPos    = taskId                                           # 外层第二轴 = seqPos
qHeadBase = kvHead * G
qRows     = G                                               # M = group
# task: {bz, kvHead, qHead=qHeadBase, qRowStart=seqPos, qRows=G, kvPos...}
```

---

## 6. 正确性红线

### 6.1 GQA head 映射

golden 的 GQA 多为**交错布局**：`head_index = kvHead · G + groupId`（`k.unsqueeze(3).expand(...,G,...).reshape(B, S_kv, N_q, D)`）。group-pack 后 M 行 `i` 的 head 必须是 `kvHead·G + i`，与 golden 一致。注意 `kvHead` 须由 task 内 `(bz, kvHead)` 解出，`N_kv>1` 时不可省（§7 陷阱 3）。

### 6.2 causal mask 的 seqPos 一致性

group-pack 下同一 task 的所有 M 行（group head）处于**同一 `seqPos`**，故 causal 阈值对所有行一致：

```text
jThresh = seqPos + causalOffset - kvStart          # 对 task 内所有 M 行相同
# 旧行号 i（序列维）已并入 seqPos，jThresh 不再随 M 行 i 变化
```

错误写法（漏改）：仍用 `globalI = seqPos + rowIdx`（把 group head 当序列行），会导致 mask 阈值随 head 偏移、大面积 mismatch（§7 陷阱 2）。

### 6.3 输出写回的 head 寻址

行 `i` → `y[bz, seqPos, qHeadBase + i, :]`。

- BSND：固定 `seqPos`，`qHeadBase..qHeadBase+groupRows` 个 head 物理连续 → **批量 `DataCopy`**（一次写 `groupRows·d`）。
- BNSD：head 维跨 `S` → 逐 head 写（`head-stride = S·d`）。
错误写法：沿用"序列行连续"的批量写公式，会把多个 head 写到错误 GM 偏移（§7 陷阱 4）。

### 6.4 Nd2Nz srcDValue 上限

`LoadNdGmToNzL1` 的 `srcDValue = headStride` 受 `uint16` 限制（≤65535）。超限时（BNSD 长 prefill）**不可**强用单次 `Nd2Nz`，必须走 §3.2 的不可 group-pack 分支或逐 head 装载兜底。

### 6.5 数值正确性

不改 scale、mask 数学、softmax 归约、累加顺序、输出 dtype/布局。group head 进 M 后浮点累加顺序变化允许 ≤atol 微小差异。

---

## 7. 已知陷阱

### 陷阱 1：BNSD 长 prefill 强行 group-pack 致 strided gather 劣化

问题：对 head-stride 超 `Nd2Nz srcDValue` 上限的 layout（BNSD 长 prefill，`S·d > 65535`）仍 group-pack + 逐 head 装载。
症状：DMA 条数随 `G·S` 爆炸，整体显著劣化。
修复：用 §3.2 的可 group-pack 判据，超限时退回序列维兜底路径（M=序列维）。两条路径共存，BNSD 长 prefill 不劣化。

### 陷阱 2：causal mask 仍按序列行处理

问题：group-pack 后 M 行是 group head，但 causal 代码仍 `globalI = seqPos + rowIdx`。
症状：mask 阈值随 head 偏移，prefill causal 大面积 mismatch。
修复：`globalI = seqPos`（常数），所有行同一阈值（§6.2）。

### 陷阱 3：N_kv>1 时 head 映射漏 kvHead

问题：`G = N_q/N_kv < N_q`，仍写 `qHead = groupId`（漏 `kvHead·G`）。
症状：N_kv>1 的 GQA case 全错；N_kv=1 巧合正确。
修复：`qHeadBase = kvHead·G`，M 行 `i` → `kvHead·G + i`（§6.1）。

### 陷阱 4：输出写回沿用序列行连续公式

问题：BSND 下 head 维连续，却用 BNSD 序列行连续的批量写公式（或反之）。
症状：输出写错 GM 偏移，整 head 错位。
修复：按 layout 与 M 维语义导出写回偏移（§6.3）；BSND-head 连续批量写，BNSD-head 逐 head 写。

### 陷阱 5：G > BLOCK_M 时 M tile 未拆分

问题：`G > BLOCK_M` 时仍 `mBaseSize = G`，Q tile 超 L1。
症状：buffer 越界 / 编译失败。
修复：`mBaseSize = min(G, BLOCK_M)`，group 维拆 `ceil(G/BLOCK_M)` 个 M tile，每 tile 复用同一 KV。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 注意力形态 | 是否 GQA/MQA？`G = N_q/N_kv` 取值；MHA(`G=1`) 不适用 |
| Cube 形态 | 手写 `LoadData`+`Mmad` 还是 Matmul 高阶 API（M 轴 tiling 是否可控） |
| group 规模 | `G` vs `BLOCK_M`；`G > BLOCK_M` 时的 M tile 拆分方案 |
| Q head 连续性 | head-stride（按 layout 推导）是否 ≤ 65535；可 group-pack 判据取值 |
| layout 分支 | BSND vs BNSD 的 Q 载入/causal/写回公式；超限时的序列维兜底 |
| causal 语义 | mask 是否随 seqPos 变化（group-pack 后对所有行一致） |
| softmax 行独立 | softmax 是否沿 K 逐行归约（head 进 M 行的必要条件） |
| L1 容量 | `G·D_qk·sizeof(T)` 等 Q/P/L0C 核算 |
| 瓶颈定位 | decode 是否 M 欠载（profiling Cube `aic_mac` 利用率低）；KV 是否重复装载 |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 改变 scale、mask 数学、softmax 归约、累加顺序、输出 dtype/布局。
- 对 head-stride 超 `Nd2Nz srcDValue` 上限的 layout 强行 group-pack（§7 陷阱 1）。
- group-pack 后 causal 仍按序列行处理（§7 陷阱 2）/ 写回沿用旧公式（§7 陷阱 4）。
- `G > BLOCK_M` 时不拆 M tile（§7 陷阱 5）。
- 同一轮混入 K 维切分、buffer 深度、同步删减、Vector 数学等改动。

回退或缩小策略的条件：

- head-stride 超限且序列维兜底不可用 → 整体退回基线。
- 精度失败且定位到 §7 陷阱 2/3/4 单一原因 → 修该原因后重试。
- `G·D_qk` 超 L1 且无法拆 M tile → 不可套用。
- decode 未明显提速且 profiling 显示 Cube `aic_mac` 利用率未升 → M 轴未真正撑满，重新归因。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>            # 编译算子
bash <build> --soc=<soc> --op=<op> --wheel    # 编译 pta
source <set_env>
pytest <op>/test/test_<op>.py                 # 精度
pytest <op>/test/test_<op>_perf.py            # 性能
```

精度：与基线一致（沿用算子既有 `atol/rtol`），含 GQA(`N_kv>1`)、causal、BNSD、zero-input 等边界 case。

性能（**必须覆盖 decode 与 prefill 两类，且无劣化**）：

- decode / 小 `S`：整体 `Task Duration` 显著下降，Cube `aic_mac` 利用率明显上升、task 数明显下降。
- prefill：整体持平或下降（来自 Q 连续装载 + task 数下降）。
- **BNSD 长 prefill（head-stride 超限）必须不劣化**（走序列维兜底）；若劣化说明可 group-pack 判据或兜底路径有误（§7 陷阱 1）。

性能结论必须写清基线与 layout 分支：

```text
本策略收益相对"每 head 一个 task、M=序列维"基线；判据是 decode M 撑满 + KV 跨 group 复用。
BNSD 长 prefill 走序列维兜底，性能不劣化是硬指标（不是可选项）。
后续 L1 操作数复用策略须相对"本策略后"评估，不能回到旧基线作增量起点。
```

## 检索卡（短卡）

动作：由每个query head独立任务改为将group维打包进Cube M轴，mBaseSize取G或min(G,BLOCK_M)
适用：GQA/MQA中G=N_q/N_kv为整数，且多个query head共享一组KV
限制：BLOCK_M=128；使用所述head布局时，须保持head_index=kvHead·G+groupId。
范围：GQA/MQA注意力的Cube矩阵乘
检索词：GQA、MQA、group维、Cube M轴、Mmad、BLOCK_M
机会：默认tiling按query head或序列块独立建任务，Cube M轴仅承载序列维
