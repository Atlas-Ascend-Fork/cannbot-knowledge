---
type: Optimization
title: 输出循环不变操作数装载外提与 L1 驻留（hoist loop-invariant GM→L1 load + L1-resident reused tile）
description: 将输出N循环内不变操作数的GM→L1 LoadData删除并外提到循环前。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/02-hoist-n-invariant-operand-load-out-of-output-loop.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：输出循环不变操作数装载外提与 L1 驻留（hoist loop-invariant GM→L1 load + L1-resident reused tile）

> **单一优化点：** 在手写 `LoadData`(GM→L1) + `LoadData`(L1→L0) + `Mmad` 驱动的 Cube 分块矩阵乘 `C = A @ B` 中，若**左操作数 `A` 不随输出 N 维（C 的列块循环）变化**（只有 `B` 的列随 N 变），把 `A` 的 GM→L1 装载从 N 循环体内**外提到循环前**（只装一次），循环内复用同一 L1 tile。对称地：若 `B` 不随输出 M 维变化，把 `B` 外提到 M 循环前。等价于经典循环不变代码外提（loop-invariant code motion）施加于 Cube 的 GM→L1 装载。
>
> **多 tile 推广（原 09-l1-resident-reused-operand-tile 已并入）：** 当不变操作数不止一个 tile（同一 task 内多个 reduce/K tile 被多个输出微块重复消费）时，把外提推广为**独立预装循环 + 多槽 L1 缓存数组**（`rhsCache[kCount]`）：微块循环前用专属 k 循环把全部 reduce tile 预装进 L1，跨全部输出微块复用，全部消费者完成后统一释放。单 tile（`kCount=1`）时严格退化为外提基线。
>
> **与"循环重排复用"（`07-cube-loop-reorder-for-l1-operand-reuse.md`）的区别：** 本策略**不重排循环层序**——N 不变性是 `A@B` 分块计算中**天然存在**的（`A` 形状 `[M,K]` 与 N 无关），只需把"每 N 块重装 `A`"改为"循环外装一次"。因此本策略适用于任何"N 循环内重复装载同一 `A`"的基线，无需也不改变 M/N 层序、L0C 结构、Fixpipe 语义。
>
> **算子无关性：** 适用于**所有**分块 Cube matmul（`QK^T`、`PV`、任意 GEMM），只要存在一个"输出维循环 + 一个不随该维变化的操作数"的组合；多 tile 推广适用于各类 attention-like kernel 的矩阵阶段（forward 的 V tile、backward 的 K/V/dO tile、多头潜空间类变体的 latent tile，或任何"同一归约 tile 被多个输出微块复用"的操作数）。

本策略只改"某个操作数的 GM→L1 `LoadData` 从输出维循环体内移到循环前（单 tile），或'预装循环 + 多槽 L1 缓存数组'（多 tile）"。不改变 L1 布局、L0A/L0B/L0C 结构、TQue 双缓冲、跨核同步、循环层序、M/K 维切分、Fixpipe 语义、微块执行顺序。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

分块 Cube matmul 常按输出 N 维（C 的列块）循环，循环体内装载两个操作数再 Mmad：

```text
LoadData B -> l1B (一次)                      # B 随 N 变，循环外装（或循环内随 nBlock）
for nBlock in N step N_TILE:                  # 输出 N 列块
    LoadData A -> l1A                          # <-- 问题：A 不随 nBlock 变，却每块重装
    for ki in K:
        LoadData l1A -> l0A ; LoadData l1B[nBlock] -> l0B
        Mmad(cL0, l0A, l0B, ...)
    Fixpipe cL0 -> C[..., nBlock]
```

`A` 的形状 `[M, K]` 与 N 无关，`nBlock` 只影响 `B` 的列与 `C` 的输出列。但基线为"对称/简洁"把 `A` 也放进 N 循环每块重装，导致：

- **GM→L1 搬运量放大 `nTiles` 倍**：`A` 被装 `nTiles = N/N_TILE` 次，而其内容每次相同。
- **Cube `aic_mte2`(GM→L1) 偏高**：重复装载 `A` 占满 MTE2 带宽，挤压 `B` 的有效装载。

典型症状：profiling 显示 `aic_mte2_time` 偏高，且 `A` 的 tile 容量小（如 attention 的 `P` 仅 `[M,K]` 几十字 KB），重装开销看似"小"但乘以 `nTiles·任务数` 后显著。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| L1 单缓冲持久化 | `A` 装载一次进 L1 后，L1 SRAM 内容持久保留至被覆盖；N 循环内重复 `LoadData`(L1→L0) 读取同一 tile |
| L0A 双缓冲 | N 循环内每块的 `LoadData`(L1→L0A) 沿用原 TQue 双缓冲，`AllocTensor/EnQue/DeQue/FreeTensor` 自管理 L0A slot |
| MTE2 带宽 | `A` 的 GM→L1 装载从 `nTiles` 次降到 1 次，省 `(nTiles−1)/nTiles` 的 `A` 搬运 |

核心改动（仅外提一行 `LoadData` + 删除循环内的对应行）：

```text
LoadData B -> l1B (一次)
LoadData A -> l1A (一次, 外提)               # <-- 从循环体内移到循环前
for nBlock in N step N_TILE:
    for ki in K:
        LoadData l1A -> l0A ; LoadData l1B[nBlock] -> l0B
        Mmad(cL0, l0A, l0B, ...)
    Fixpipe cL0 -> C[..., nBlock]
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 计算形态 | 分块 Cube matmul，存在"输出维循环"（N 或 M） |
| 操作数不变性 | 某操作数（`A` 对 N 循环，或 `B` 对 M 循环）的 GM 地址/形状**不随该输出维循环索引变化** |
| 单缓冲安全 | 该操作数的 L1 单缓冲在 N 循环内**不被其它阶段覆盖**（见 §6.1 / §7 陷阱 1） |
| L1→L0 同步 | N 循环内读该操作数的 `LoadData`(L1→L0) 沿用原 TQue 双缓冲语义（不依赖每块 GM→L1 的 `SetWaitFlag`） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- N 维 tile 数较多（`nTiles = N/N_TILE ≥ 2`，如 `N=512, N_TILE=128 → 4`）；`nTiles=1` 时无收益也无害。
- 不变操作数 tile 较小但任务数大（重复装载的绝对量随任务数放大）。
- 多 tile 推广：一个 reduce tile 被 2 个以上 M/N 微块消费；tile 数量固定且小（如 2 个 K/V slice 被 4 个 M 微块复用）；当前实现每个微块都 `Alloc/Load/Free` 同一个 operand tile。

不适用或需先重构：

- 两操作数都随输出维变化（无不变操作数可外提）。
- 不变操作数的 L1 单缓冲在 N 循环内会被**同 Cube 阶段的其它装载**覆盖（需先做缓冲隔离或双缓冲，属另一策略）。
- 该装载走 Matmul 高阶 API（其 GM→L1 由框架管，不在 kernel 手写）。
- 目标收益来自 K 维切分、循环重排、跨核同步、Vector 侧——非本策略。
- 多 tile 推广额外不适用：operand tile 随输出微块改变，无法跨微块复用；operand 只被消费一次；缓存会改变 sparse/mask/dropout/causal 边界的有效数据范围（须按真实有效 tile 加载，不读越界 GM）；为实现缓存必须改变分核、tile shape 或数学公式。

---

## 3. 外提判据与候选识别

### 3.1 不变性判据

对每个输出维循环（记索引 `i`，遍历 `A` 的列块或 `B` 的行块），逐一检查两操作数的 GM 装载：

```text
# 候选：左操作数 A 对 N 循环不变
A_gm_offset(i)  与 i 无关 ?   # A 的 GM 起址不随 nBlock 变
A_shape(i)      与 i 无关 ?   # A 的 m/k 不随 nBlock 变
→ 满足则 A 可外提到 N 循环前
# 对称：右操作数 B 对 M 循环不变（若有 M 循环）
```

### 3.2 示例（attention 的 `P@V` 阶段）

```text
A = P (softmax 输出), 形状 [M, K]      # K 维 = KV 行数，不随输出 N 维变化
B = V,                形状 [K, N]
for nBlock in N step N_TILE:           # N 循环 = N/N_TILE 块
    # 基线：每块重装 P（P 内容对所有 N 块相同，仅 V 列变化）
    # 外提：P 移到循环前装一次，循环内复用
```

`P` 对 N 循环不变（`P=[M,K]`，N 维只进 `V`/`C`），是典型候选。`V` 本身在基线已装一次（循环外），无需动。

---

## 4. 数据与缓存布局

### 4.1 不变操作数的 L1 生命周期

外提后，不变操作数（如 `P`）的 L1 tile 在 N 循环内**持久驻留**，被每块的 `LoadData`(L1→L0A) 反复读取：

```text
l1A = pL1Buf.Get()                          # 循环前
LoadData(pL1, wsP[...], m=M, n=K, ...)      # 循环前，GM->L1 一次
for nBlock:
    l0A = AllocTensor ; LoadData l1A -> l0A ; ...   # 循环内，L1->L0 每 K tile
```

### 4.2 容量核算

单 tile：不变操作数 tile 字节 = `M_align · K_align · sizeof(T)`，须 ≤ 其 L1 单缓冲（外提前后该 tile 大小不变，故容量不变，仅装载频次下降）。

多 tile：L1 须同时容纳 **kCount 个缓存 tile**（`kCount · operand_tile_bytes`）+ 当前微块专属 tile + 原有队列/scratch。容量不足时缓存会挤掉更关键的 double buffer，须先削减 kCount 或放弃。

### 4.3 收益估算（多 tile）

```text
old_load_count = output_micro_tile_count * reduce_tile_count
new_load_count = reduce_tile_count
saved_loads = old_load_count - new_load_count
saved_bytes = saved_loads * operand_tile_bytes
```

若 `saved_loads <= 0` 或 `saved_bytes` 小于测量噪声，不实施。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| Cube MM 函数 N 循环 | 删除循环体内的"不变操作数 `LoadData`(GM→L1)"；在循环前（与其它循环外装载并列）加一次该 `LoadData` |
| N 循环内 K 子循环 | 不变（`LoadData`(L1→L0) + `Mmad` 语义不变） |
| L1→L0 helper | 通常不改（helper 已支持循环内多次读同一 L1 tile） |
| 同步 | 把原伴生于该 GM→L1 装载的 `SetWaitFlag<MTE1_MTE2>`/`<MTE2_MTE1>` 对**随装载一起外提**到循环前；循环内不再发（见 §6.2） |

### 5.2 通用 N 循环改写

```text
# 基线
LoadData vL1 <- V (一次, 循环外)
for nBlock in nTiles:
    SetWaitFlag<MTE1_MTE2> ; LoadData pL1 <- P (GM->L1) ; SetWaitFlag<MTE2_MTE1>   # 每块重装
    cL0 = AllocTensor
    Mmad(pL1, vL1[nBlock], cL0, ...)
    Fixpipe(cL0 -> wsO[nBlock])

# 改写后（P 外提）
LoadData vL1 <- V (一次)
SetWaitFlag<MTE1_MTE2> ; LoadData pL1 <- P (GM->L1, 一次, 外提) ; SetWaitFlag<MTE2_MTE1>
for nBlock in nTiles:
    cL0 = AllocTensor
    Mmad(pL1, vL1[nBlock], cL0, ...)        # pL1 复用，vL1 按 nBlock 取列
    Fixpipe(cL0 -> wsO[nBlock])
```

`vL1`（随 N 变的操作数）的取列偏移按其 L1 NZ 布局导出（如 `vL1Base = nBlock · K_align · N_TILE`），与基线一致。

### 5.3 多 tile 推广改写（预装循环 + 多槽缓存数组）

当同一 task 内多个 reduce/K tile 被多个输出微块重复消费时（原 09-l1-resident-reused-operand-tile 场景），把单 tile 外提推广为多槽缓存：

低效模式（每个微块重复 `Alloc/Load/Free` 同一批 reduce tile）：

```cpp
for (uint32_t m = 0; m < mCount; ++m) {
    for (uint32_t k = 0; k < kCount; ++k) {
        auto rhsL1 = rhsQue.AllocTensor<T>();
        LoadRhsTile(rhsL1, task, k);
        rhsQue.EnQue(rhsL1);
        rhsL1 = rhsQue.DeQue<T>();

        auto lhsL1 = LoadLhsForMicroTile(task, m, k);
        ComputeMmad(lhsL1, rhsL1, m, k);

        rhsQue.FreeTensor(rhsL1);
    }
}
```

推荐模式（预装 + 驻留 + 统一释放）：

```cpp
LocalTensor<T> rhsCache[MAX_REDUCE_TILES];

for (uint32_t k = 0; k < kCount; ++k) {          // 独立预装循环
    rhsCache[k] = rhsQue.AllocTensor<T>();
    LoadRhsTile(rhsCache[k], task, k);
    rhsQue.EnQue(rhsCache[k]);
    rhsCache[k] = rhsQue.DeQue<T>();
}

for (uint32_t m = 0; m < mCount; ++m) {          // 计算循环：顺序与基线一致
    bool firstReduce = true;
    for (uint32_t k = 0; k < kCount; ++k) {
        auto lhsL1 = LoadLhsForMicroTile(task, m, k);
        if (!firstReduce) {
            PipeBarrier<PIPE_M>();               // 只有首个 reduce tile 免 barrier（初始化语义）
        }
        ComputeMmad(lhsL1, rhsCache[k], m, k, firstReduce);
        firstReduce = false;
        FreeLhsForMicroTile(lhsL1);
    }
}

for (uint32_t k = 0; k < kCount; ++k) {          // 全部消费者完成后统一释放
    rhsQue.FreeTensor(rhsCache[k]);
}
```

要点：

- **计算循环顺序不变**：只独立化装载循环，不改微块执行顺序（不需要证明累加语义等价）。
- **`PipeBarrier<PIPE_M>` + `firstReduce`**：只有第一个 reduce tile 以 `cmatrixInitVal` 初始化 L0C（无前序生产者），后续 tile 间才需 barrier 保累加顺序（详见 `07-redundant-sync-elimination-compact.md` 的 PIPE_M 专节）。
- **TQue 多持限制**：若 `TQue` 不能安全持有多个已 `DeQue` 未 `Free` tensor，可改为 `TBuf<TPosition::A1/B1>` 静态切片，但必须显式补齐 HardEvent 生命周期；不要混用 TQue 的隐式同步语义和裸 TBuf。
- **释放时机**：不要在每个微块结束时释放 cached operand；须等全部消费者完成。

---

## 6. 正确性红线

### 6.1 单缓冲覆盖安全（正确性关键）

不变操作数的 L1 单缓冲（如 `pL1Buf`）在 N 循环内必须**不被同阶段的其它 GM→L1 装载覆盖**。逐阶段证明：

- 若该缓冲在 N 循环内只被"本操作数的 L1→L0 读"使用（无其它 GM→L1 写），外提安全。
- 若同阶段有其它装载共用该缓冲，必须先做缓冲隔离（换缓冲或双缓冲），否则外提后循环内读到的会被覆盖（§7 陷阱 1）。

### 6.2 同步与生命周期

- 伴生于不变操作数 GM→L1 的 `SetWaitFlag<MTE1_MTE2>`（等前 MTE1 完成再 MTE2 写）与 `<MTE2_MTE1>`（等 MTE2 完成再 MTE1 读）**成对外提**到循环前；循环内删除，避免每块发空同步拖慢流水。
- L1→L0 沿用原 TQue 双缓冲（`AllocTensor/EnQue/DeQue/FreeTensor`），同步语义不变。
- 不删除任何跨核 flag 或 queue acquire/release。

### 6.3 数值正确性

不改变 Mmad 的 K 归约顺序、累加初值（`cmatrixInitVal`）、Fixpipe 语义、输出 dtype/布局。外提只减少重复装载次数，不改数学。

### 6.4 边界处理

N 维尾块（`N % N_TILE != 0`）沿用基线尾块处理；外提的不变操作数对尾块同样有效（其形状不随 N 变）。M/K 维尾块不在本策略修改。

---

## 7. 已知陷阱

### 陷阱 1：单缓冲在 N 循环内被同阶段其它装载覆盖

问题：外提后，不变操作数的 L1 缓冲在 N 循环内被另一 GM→L1 装载（同 Cube 阶段）覆盖。
症状：循环内读到错误数据，mismatch 集中在对应 N 块。
修复：实施前按 §6.1 证明该缓冲在 N 循环内无其它 GM→L1 写；若共用，先换缓冲或双缓冲。

### 陷阱 2：误把"随 N 变"的操作数外提

问题：把 `vL1`（随 nBlock 取列）当成不变操作数外提，循环内不更新列偏移。
症状：所有 N 块用同一列，输出列错位。
修复：按 §3.1 不变性判据严格区分；只外提 GM 地址/形状都不随循环索引变的操作数。

### 陷阱 3：漏外提伴生 SetWaitFlag 致流水扰动

问题：外提了 `LoadData` 但把 `SetWaitFlag` 对留在循环内（或反之）。
症状：MTE2/MTE1 同步错位，偶发数值错或性能未达预期。
修复：`LoadData` 与其 `SetWaitFlag` 对**一起**外提或一起留（§6.2）。

### 陷阱 4：nTiles=1 时误判有收益

问题：`N` 恰为 `N_TILE` 倍数且 `nTiles=1`（如 `N=128` 且 `N_TILE=128`），外提无实际收益却被当作优化。
诊断：`nTiles=1` 时外提等价（装载本就一次），整体 µs 不变属正常，非策略失效。
修复：收益评估以 `nTiles≥2` 的 case 为准。

### 陷阱 5（多 tile）：L1 容量压力 / queue depth 不足

问题：kCount 个缓存 tile 驻留后挤占 L1，或 TQue depth 不支持多 tensor 持有，出现 L1 overwrite、随机 hang。
症状：mismatch 随机分布、偶发 hang、性能回退。
修复：按 §4.2 核算 kCount 容量；Task Duration 回退时检查 L1 容量压力、queue depth 和释放点；TQue 不可多持时退化为 TBuf 静态切片 + 显式 HardEvent（§5.3）。

### 陷阱 6（多 tile）：误把"随微块变化"的 operand 当可复用 tile 缓存

问题：把随输出微块变化的 operand 错当成可复用 tile 装进 `rhsCache`，各微块读到同一份数据。
症状：输出按微块整体错位。
修复：按 §3.1 不变性判据严格区分；只有 GM offset 与输出微块索引无关的 tile 才可缓存。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 计算形态 | 哪个 Cube matmul 阶段有"输出 N（或 M）循环" |
| 不变性候选 | 哪个操作数对该循环不变（GM 地址 + 形状都不随循环索引变） |
| nTiles | `N/N_TILE`（或 `M/M_TILE`）取值；`nTiles=1` 无收益 |
| 单缓冲安全 | 该操作数 L1 缓冲在循环内是否被同阶段其它装载覆盖（§6.1） |
| 伴生同步 | 该装载的 `SetWaitFlag` 对位置（随 `LoadData` 一起外提，§6.2） |
| 尾块 | N 维尾块是否沿用基线处理 |
| 基线可重复 | 修改前 build/精度/性能基线值 |
| 多 tile 推广 | 同 task 内该 operand 被几个输出微块复用；kCount 与 L1 驻留峰值字节数（§4.2）；安全加载点/释放点在哪个循环边界（§5.3） |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 外提"随循环变"的操作数（§7 陷阱 2）。
- 在单缓冲会被同阶段覆盖时外提而不先隔离缓冲（§7 陷阱 1）。
- 把 `LoadData` 与其 `SetWaitFlag` 对拆开外提（§7 陷阱 3）。
- 改变 Mmad 归约顺序、`cmatrixInitVal`、Fixpipe 语义、输出 dtype/布局。
- 同一轮混入 K 维切分、循环重排、buffer 深度、跨核同步改动。

回退或缩小策略的条件：

- 单缓冲覆盖无法隔离 → 不外提（退回基线或先做缓冲隔离）。
- 精度失败且定位到 §7 陷阱 1/2/3 单一原因 → 修该原因后重试。
- `nTiles=1` → 无收益，外提与否等价（§7 陷阱 4），不作为劣化。
- profiling 显示 `aic_mte2` 未下降 → 该操作数本就未重复装载或装载非瓶颈，重新归因。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>
bash <build> --soc=<soc> --op=<op> --wheel
source <set_env>
pytest <op>/test/test_<op>.py
pytest <op>/test/test_<op>_perf.py
```

精度：与基线一致。

性能：

- 整体 `Task Duration` 在 `nTiles≥2` 的 case 上下降；`nTiles=1` 的 case 持平（正常）。
- profiling Cube `aic_mte2_time`（GM→L1）相对基线下降（不变操作数装载频次 `/nTiles`）。
- 多 tile 推广：目标 operand 的 GM→L1 次数下降到理论值（`reduce_tile_count` 次/task）；AIC MTE2 指令数或 GM→L1 字节数下降；Cube FOPs 不增加；建议记录 `old/new_operand_loads_per_task`、`saved_gm_to_l1_bytes`、`AIC MTE2 instruction count`、`Cube time`、`Task Duration`。
- **无任何 case 劣化**（外提只减装载，不应引入劣化；若劣化说明伴生同步处理有误，§7 陷阱 3；多 tile 场景检查 §7 陷阱 5）。
- 多 tile 精度：全量通过，含 tail、mask、GQA/MQA head mapping、latent/head 维度映射、反向累加 case；无 L1 overwrite、queue depth 不足、随机 hang。

性能结论必须写清基线与 `nTiles`：

```text
本策略收益相对"每 N 块重装不变操作数"基线；判据是 nTiles≥2 的 case 整体 µs 下降 + aic_mte2 下降。
nTiles=1 的 case 持平属正常。后续策略须相对"本策略后"评估。
```

## 检索卡（短卡）

动作：将输出N循环内不变操作数的GM→L1 LoadData删除并外提到循环前。
适用：分块Cube matmul存在N或M输出维循环。
限制：须保证不变操作数L1单缓冲的覆盖安全。
范围：LoadData与Mmad驱动的Cube分块矩阵乘。
检索词：Cube matmul、LoadData、GM→L1、L1→L0、L1单缓冲、N循环。
机会：输出维循环内重复执行不变操作数的GM→L1装载。
