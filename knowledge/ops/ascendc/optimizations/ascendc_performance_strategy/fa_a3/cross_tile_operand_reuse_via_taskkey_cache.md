---
type: Optimization
title: 跨内层迭代操作数复用（task-key 缓存跳过重载，带场景 gating）
description: 加入 task-key 命中判断，将操作数由逐迭代装载改为跨 tile 复用。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/03-cross-tile-operand-reuse-via-taskkey-cache.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：跨内层迭代操作数复用（task-key 缓存跳过重载，带场景 gating）

> **单一优化点：** 在 Cube 流水线（ring/软件流水跨核或跨阶段）中，若某操作数（如 `QK^T` 的左操作数 `Q`）对**连续的内层迭代**（如同一 `(bz,head,seqPos)` task 的连续 KV-tile）**不变**，则用"上一次装载的 task 标识 key"做缓存：连续命中同一 key 时**跳过该操作数的 GM→L1 `LoadData` 重载**，复用 L1 中已驻留的 tile。task 切换时 key 变化 → 强制重载，保证只对"真正连续的同 task 迭代"命中。
>
> **与"循环重排复用"/"装载外提"两类策略的区别：** 本策略是**跨 Cube 调用（跨 ring 迭代）**的 L1 持久化复用——内层迭代由顶层调度/ring 驱动，非单个 MM 函数内的循环；复用靠 task-key 命中而非循环重排或装载外提。三者层级不同：装载外提是单 MM 函数内 N 循环外提；循环重排是单 MM 函数内 M/N 层序重排；本策略是跨 ring 迭代的缓存命中。
>
> **关键 gating（必须）：** 只在内层迭代数较大（带宽主导）时启用；内层迭代数小时，该装载本与 Cube 计算良好重叠，跳过会扰动 MTE2/MTE1 流水节拍，**净劣化**。gating 用"内层迭代数阈值"控制。
>
> **算子无关性：** 适用于**所有**"内层迭代共享某 Cube 操作数"的 AscendC 流水（attention 的 `Q` 跨 KV-tile、卷积的 weight 跨 tile 等），只要该操作数的 L1 单缓冲满足"仅本装载写、仅本 L0 读"的隔离契约。

本策略只改"某操作数 GM→L1 装载加 task-key 命中判断 + 跳过"。不改变 L1 布局、L0A/L0B/L0C 结构、TQue 双缓冲、ring 流水、跨核同步、循环层序、M/N/K 维切分。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

Cube 流水线（如 attention 的 ring：`cur=MM1, prev1=MM2+Vec1, prev2=Vec2`）按内层迭代（KV-tile）推进，每迭代调用 MM 函数：

```text
for iter in inner_loop:                 # 内层迭代 = s2 tile，由 ring 驱动
    Q = load Q[task]                     # <-- 问题：Q 对同一 task 的所有 iter 不变，却每 iter 重载
    K = load K[task, s2(iter)]           # K 随 s2 变
    Mmad Q@K^T ; ...                     # mm1
```

当内层迭代属同一 task（如 `(bz,head,seqPos)` 固定，只有 `s2` 变）时，`Q` 跨迭代不变，却每迭代从 GM 重装进 L1。GM→L1 搬运量放大 `innerCount` 倍（如 KV 长度 2048、tile 长 128 时放大 16 倍）。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| L1 SRAM 持久化 | L1 单缓冲内容在未被覆盖前持久保留；跨 ring 迭代（同 task）复用已驻留 tile |
| 单缓冲隔离契约 | 该操作数缓冲"仅本装载(MTE2)写、仅本 L0(MTE1)读"→ 连续同 task 迭代间无其它写，跳过安全 |
| task-key 命中 | 缓存上一次装载的 task 标识；连续命中则跳过；task 变则强制重载 |

核心改动（MM 函数入口加 key 判断）：

```text
curKey = taskKey(task)                       # (bz, head, seqPos) 等唯一标识
if not (cached and curKey == lastKey):       # 首次或 task 变 → 装载
    LoadData Q -> l1Q (GM->L1)
    lastKey = curKey ; cached = true
# 连续同 task 迭代：跳过 LoadData，复用 l1Q
Mmad(l1Q, l1K[s2], ...)                       # mm1
```

### 1.3 为什么必须 gating（场景判据）

跳过装载同时跳过了伴生的 `SetWaitFlag<MTE1_MTE2>`/`<MTE2_MTE1>`，改变了 MTE2/MTE1 的交错节拍：

- **内层迭代多（带宽主导）：** 装载是瓶颈，跳过省带宽，净收益。
- **内层迭代少（计算主导）：** 装载本与 Cube 计算良好重叠，跳过后 MTE2 空窗打乱重叠，**净劣化**（小迭代数场景实测出现过数个百分点的劣化）。

故按内层迭代数阈值 gate：`innerCount ≥ THRESH` 才启用。

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 流水形态 | Cube 操作数跨"连续内层迭代"不变，且内层迭代由顶层调度/ring 驱动（非单 MM 函数内循环——那属于装载外提/循环重排类策略） |
| 单缓冲隔离 | 该操作数 L1 单缓冲"仅本装载写、仅本 L0 读"，连续同 task 迭代间无其它 GM→L1 写覆盖（见 §6.1 / §7 陷阱 1） |
| task 可键化 | 存在唯一 task 标识（如 `(bz, head, seqPos)`）可编码为 key，且"同 task 连续迭代"在调度顺序中**真连续**（见 §6.2 / §7 陷阱 2） |
| 场景 gating | 内层迭代数 ≥ 阈值时启用；否则关闭（避免流水扰动劣化） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- 内层迭代数大（如 KV 长度 2048、tile 长 128 → 16 次内层迭代）：省 `(innerCount−1)/innerCount` 的该操作数搬运。
- 该操作数 tile 较大（装载开销显著）。
- 该操作数在内层迭代中确为瓶颈（profiling `aic_mte2` 中其装载占比高）。

不适用或需先重构：

- 该操作数在内层迭代中**随迭代变化**（无可复用性）。
- 单缓冲在连续迭代间会被同阶段其它装载覆盖（§7 陷阱 1）。
- 同 task 的迭代在调度顺序中**不连续**（被其它 task 隔开）——此时 key 命中不会发生，策略 no-op（§7 陷阱 2）。
- 内层迭代数小且装载与计算重叠良好——不启用（gating 关闭）。
- 目标收益来自循环重排、装载外提、K 维切分、Vector 侧——非本策略。

---

## 3. task-key 与 gating 设计

### 3.1 key 编码

把"使该操作数不变的 task 维度"编码为整数 key。对 attention 的 `Q`（跨 `s2` 不变，随 `(bz, head, seqPos)` 变）：

```text
key = (bz << off1) | (head << off2) | seqPos      # 唯一标识 (bz, head, seqPos)
# 各字段位宽按取值范围分配（bz≤B, head≤N_q, seqPos≤S）；task 变 → key 变 → 强制重载
```

`lastKey` + `cached` 作为 MM 函数所在类的成员，跨 ring 迭代持久。

### 3.2 连续性前提

key 命中要求"同 task 的内层迭代在调度顺序中连续"。attention 的内层循环顺序为 `(bz, head, seqPos, s2-inner)`——同 `(bz,head,seqPos)` 的 `s2` 迭代真连续，故命中成立。若调度顺序把同 task 迭代隔开（如 `s2` 外层、`seqPos` 内层），命中不发生（§7 陷阱 2），策略退化 no-op（无害但无收益）。

### 3.3 gating 阈值

```text
innerCount = CeilDiv(内层轴总长, tile 长)         # 内层迭代数（attention 场景为 KV 轴 / s2 tile 数）
enableReuse = innerCount ≥ THRESH
qReuse = cached and (curKey == lastKey) and enableReuse
```

阈值选取：在"内层迭代多（带宽主导）"与"少（计算主导）"的分界处。无 profiling 时取使大小两端都不劣化的值。

---

## 4. 数据与缓存布局

### 4.1 复用 tile 的 L1 生命周期

被复用的操作数 tile（如 `qL1`）在首次装载后驻留 L1，跨连续同 task 迭代被反复 `LoadData`(L1→L0A) 读取：

```text
首次/ task 变: LoadData qL1 <- Q (GM->L1) + SetWaitFlag 对
连续同 task:   跳过 LoadData；qL1 内容持久保留
每 iter L1->L0: LoadData qL1 -> l0A (沿用原 TQue 双缓冲)
```

### 4.2 单缓冲隔离契约（正确性关键）

被复用缓冲（如 `qL1Buf`）必须满足：

- **仅本操作数的 GM→L1 装载写**（跳过时不写）。
- **仅本操作数的 L1→L0 读**（同 Cube 阶段的其它 MM 若用不同缓冲，则不冲突）。
- 连续同 task 迭代间，**同阶段的其它 GM→L1 装载不覆盖该缓冲**。

逐阶段证明（attention：`qL1Buf` 仅 `mm1` 的 Q 装载写、仅 `mm1` 的 L0A 读；`mm2` 用 `pL1/vL1`，不碰 `qL1`；连续 s2 迭代间 ring 调度不插入写 `qL1` 的操作 → 隔离成立）。不满足则不可套用（§7 陷阱 1）。

---

## 5. 实施步骤

### 5.1 修改位置

| 位置 | 修改 |
|---|---|
| Cube MM 函数（含被复用操作数装载处） | 入口加 `curKey` 计算 + `qReuse` 命中判断；命中则跳过该操作数的 GM→L1 `LoadData` 及其伴生 `SetWaitFlag` 对；未命中则装载并更新 `lastKey/cached` |
| MM 类成员 | 新增 `lastKey`(uint64)、`cached`(bool)，跨 ring 迭代持久 |
| Host tiling | 提供 `innerCount`（内层迭代数，如内层轴 tile 块数）供 gating 判断（已存在字段则复用） |
| 其它（ring 调度 / L0 / Vector / K 维） | **不改** |

### 5.2 通用改写

```text
# 基线（每内层迭代重装 Q）
ComputeMM1(info):
    SetWaitFlag<MTE1_MTE2>
    LoadData qL1 <- Q[info]                     # GM->L1，每 iter
    SetWaitFlag<MTE2_MTE1>
    ... K 装载 / Mmad ...

# 改写后（task-key 缓存 + gating）
ComputeMM1(info):
    curKey = taskKeyOf(info)                      # 由 task 维度组合编码
    qReuse = cached_ and (curKey == lastKey_) and (innerCount >= THRESH)
    if not qReuse:
        SetWaitFlag<MTE1_MTE2>
        LoadData qL1 <- Q[info]                 # GM->L1，仅首次/task 变
        SetWaitFlag<MTE2_MTE1>
        lastKey_ = curKey ; cached_ = true
    ... K 装载（每 iter，随 s2 变）/ Mmad（读 qL1，复用或新装一致）...
```

命中时跳过的伴生 `SetWaitFlag` 对：因无 MTE2 写，MTE1 读的是已驻留（首次装载时已 `SetWaitFlag<MTE2_MTE1>` 保证可见）的稳定 SRAM 内容，无需再同步（§6.3）。

---

## 6. 正确性红线

### 6.1 单缓冲隔离（正确性前提）

被复用缓冲必须"仅本装载写、仅本 L0 读"，连续同 task 迭代间无其它写（§4.2）。实施前逐阶段证明；不满足则不可套用（§7 陷阱 1）。

### 6.2 调度连续性

key 命中要求同 task 内层迭代在调度顺序中连续。若调度把同 task 迭代隔开，命中不发生（策略 no-op，无害）。实施前确认内层循环顺序（如 `(bz,head,seqPos, s2-inner)`）。

### 6.3 跳过装载的可见性

命中跳过装载时，L1 内容来自"该 task 首次装载"，其 MTE2 完成性已由首次装载的 `SetWaitFlag<MTE2_MTE1>` 保证。L1 SRAM 内容持久，后续 MTE1 读稳定数据，无需额外同步。不可在命中分支里留下"半截"`SetWaitFlag`（§7 陷阱 3）。

### 6.4 task 切换强制重载

`curKey != lastKey`（task 变）→ 不命中 → 强制重载并更新 key。这保证：缓冲被其它 task 的装载覆盖后，回到原 task 时不会误命中旧内容（§7 陷阱 4）。

### 6.5 数值正确性

不改变 Mmad 归约、累加、Fixpipe、输出 dtype/布局。复用只减少装载次数，被复用 tile 内容与重装一致（同一 GM 源）。

---

## 7. 已知陷阱

### 陷阱 1：单缓冲在连续迭代间被覆盖

问题：被复用缓冲（如 `qL1`）在连续同 task 迭代间被同阶段其它 GM→L1 装载覆盖，命中时读到错误数据。
症状：mismatch 集中在某些内层迭代。
修复：按 §4.2 证明隔离契约；不满足则不可套用，或先做缓冲隔离/双缓冲。

### 陷阱 2：调度顺序使同 task 迭代不连续

问题：内层循环顺序非 `(..., task-fixing dims, s2-inner)`，同 task 的 s2 迭代被其它 task 隔开，key 永不连续命中。
症状：策略 no-op（无收益也无害），但实施者误判"已优化"。
修复：确认调度顺序（§6.2）；若不连续，先调循环层序（属 sfa-09 循环重排）再套本策略。

### 陷阱 3：命中分支残留半截 SetWaitFlag

问题：跳过了 `LoadData` 却留下 `SetWaitFlag<MTE2_MTE1>`（无 MTE2 可等），或反之。
症状：MTE2/MTE1 同步错位，流水扰动或偶发数值错。
修复：`LoadData` 与其 `SetWaitFlag` 对**整块**跳过或整块保留（§5.2/§6.3）。

### 陷阱 4：task 切换后误命中旧 key

问题：`lastKey` 未在 task 变时更新，或 key 编码碰撞，回到旧 task 时误判命中、读到被覆盖后的内容。
症状：跨 task 后某些迭代 mismatch。
修复：key 编码唯一（含所有使操作数变的维度）；task 变（`curKey != lastKey`）强制重载并更新（§6.4）。

### 陷阱 5：ungated 在小迭代数场景劣化

问题：未加 gating，对内层迭代数小的场景也启用，装载本与计算重叠良好，跳过扰动流水。
症状：小迭代数 case 整体耗时上升。
修复：按 `innerCount ≥ THRESH` gate（§3.3）；阈值用 profiling 或"大小两端都不劣化"选取。

### 陷阱 6：误把"随内层迭代变"的操作数缓存

问题：把 `K`（随 s2 变）当不变操作数缓存。
症状：连续迭代用同一 K，score 错。
修复：只缓存"对该内层迭代不变"的操作数（§2）；随内层迭代变的操作数不可缓存。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 流水形态 | 哪个 Cube 操作数跨"连续内层迭代"不变；内层迭代由 ring/顶层调度驱动（非单 MM 内循环） |
| 单缓冲隔离 | 该操作数缓冲是否"仅本装载写、仅本 L0 读"，连续迭代间无覆盖（§4.2） |
| task 可键化 | 使该操作数不变的 task 维度组合；key 编码；调度顺序是否使同 task 迭代连续（§6.2） |
| 内层迭代数 | `innerCount` 取值范围；gating 阈值 `THRESH` 选取依据 |
| 伴生同步 | 该装载的 `SetWaitFlag` 对，命中时整块跳过（§5.2） |
| task 切换 | `curKey != lastKey` 强制重载 + 更新 key 的落点（§6.4） |
| 瓶颈定位 | 该操作数装载是否内层瓶颈（profiling `aic_mte2` 占比） |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 在单缓冲不满足隔离契约时套用（陷阱 1）。
- 缓存"随内层迭代变"的操作数（陷阱 6）。
- ungated 对所有场景启用（陷阱 5）。
- 命中分支残留半截 `SetWaitFlag`（陷阱 3）。
- key 编码不唯一或 task 切换不强制重载（陷阱 4）。
- 改变 Mmad 归约、累加、Fixpipe、输出 dtype/布局。
- 同一轮混入循环重排、装载外提、K 维切分、buffer 深度、同步删减改动。

回退或缩小策略的条件：

- 单缓冲隔离不成立且无法隔离 → 不套用。
- 调度顺序使同 task 迭代不连续（陷阱 2）→ 先循环重排，或策略 no-op 保留。
- ungated 小迭代数场景劣化（陷阱 5）→ 加 gating；阈值无法选到"大小都不劣化"则关闭。
- 精度失败且定位到陷阱 1/3/4/6 单一原因 → 修该原因后重试。
- profiling 显示 `aic_mte2` 未下降 → 该操作数未重复装载或非瓶颈，重新归因。

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

性能（**必须分"大迭代数"与"小迭代数"两类，且都无劣化**）：

- 大内层迭代数（`innerCount ≥ THRESH`）：整体 `Task Duration` 下降，Cube `aic_mte2` 下降。
- 小内层迭代数（`innerCount < THRESH`）：gating 关闭，整体持平（**不可劣化**；劣化说明 gating 阈值或落点有误，§7 陷阱 5）。

性能结论必须写清基线、gating 阈值与两类场景：

```text
本策略收益相对"每内层迭代重装不变操作数"基线；判据是大迭代数 case 整体耗时 + aic_mte2 下降。
小迭代数 case 由 gating 关闭，不劣化是硬指标。后续策略须相对"本策略后"评估。
```

## 检索卡（短卡）

动作：加入 task-key 命中判断，将操作数由逐迭代装载改为跨 tile 复用。
适用：Cube操作数在连续内层迭代中不变，且这些迭代由顶层调度或ring驱动。
限制：复用期间 L1 单缓冲内容不得被覆盖。
范围：Cube流水线中跨连续内层迭代不变的操作数。
检索词：L1 SRAM、task-key、curKey、qReuse、ring 迭代。
机会：KV-tile 内层循环每次都调用 MM，存在重复操作数装载。
