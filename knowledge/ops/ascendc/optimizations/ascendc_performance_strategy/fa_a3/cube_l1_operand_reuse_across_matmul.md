---
type: Optimization
title: Cube 侧多 matmul 共享操作数的 L1 跨 mm 复用
description: 将多个matmul的共享操作数改为在Cube侧L1中跨matmul复用。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/05-cube-l1-operand-reuse-across-matmul.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：Cube 侧多 matmul 共享操作数的 L1 跨 mm 复用

> **单一优化点：** 当 cube 侧一个计算阶段含多个 matmul，且某些操作数被多个 matmul 共享（同一 GM operand 被两个不同 mm 以不同角色读取，例如既作某 mm 的 A 矩阵、又作另一 mm 的 B 矩阵，或同一 operand 同时供前/后半段使用）时，baseline 每个 matmul 自包含地从 GM 重新加载全部操作数（含 ND→NZ 格式转换的 `LoadNdGmToNzL1`，其标量参数设置极重），导致**共享操作数被重复 GM→L1 搬运**（每个共享 operand 被搬 K 次，K=使用它的 mm 数）。改为：把 GM→L1 加载从各 matmul 内部抽出，集中到阶段前置一次性加载，加载后**跨多个 matmul 复用同一 L1 tensor**（持久持有 `DeQue` tensor，最后一个消费者用完才 `FreeTensor`），消除重复搬运与重复的 `LoadNdGmToNzL1` 标量设置。各 matmul 用不同的 L1→L0 读取模式（L0A/L0B、转置/不转置）复用同一份 L1 数据。

---

## 1. 已有模式与变更

### 已有模式（baseline）

cube 阶段含 N 个 matmul（分布在跨核流水的前/后半段），每个 matmul 是**自包含全流程**，各自从 GM 加载自己的 A、B 操作数到 L1，再做 L1→L0→Mmad→Fixpipe，最后 Free L1：

```text
ComputeMM_i:
  aL1 = queA.AllocTensor;  LoadNdGmToNzL1(aL1, gmA[offA]);  queA.EnQue(aL1);  aL1 = queA.DeQue
  bL1 = queB.AllocTensor;  LoadNdGmToNzL1(bL1, gmB[offB]);  queB.EnQue(bL1);  bL1 = queB.DeQue
  aL0 = ...;  LoadNzL1ToZzL0A(aL0, aL1, ...);          // 或 ZnL0B / WithTranspose
  bL0 = ...;  LoadNzL1ToZnL0B(bL0, bL1, ...)           // 角色与转置随 mm 而定
  Mmad(cL0, aL0, bL0, mp);  Fixpipe(gmOut, cL0, fp)
  queA.FreeTensor(aL1);  queB.FreeTensor(bL1)          // 每个 mm 用完即释放
```

当 `gmA`/`gmB` 被多个 mm 共享时（例如某个 operand 既在前半段某 mm 用、又在后半段某 mm 用），**每个使用它的 mm 都重新执行一次 `LoadNdGmToNzL1`**。`LoadNdGmToNzL1` 是 ND→NZ 格式转换搬运，其标量参数设置（每个 16×16 分形的 NZ 布局地址推导）开销远高于普通 `LoadData`。共享 operand 被搬 K 次 ⇒ GM→L1 搬运量与 `LoadData` 标量设置次数成倍膨胀，直接推高 `aic_mte2_time` 与 `aic_scalar_time`，且因 `depth=1` 无 ping/pong 缓存，**跨 mm 复用完全丧失**。

### 变更（v1.1）

- 【变更】把 GM→L1 加载从各 `ComputeMM` 内部抽出，集中到**阶段前置**（前半段开头加载该段全部 operand；后半段开头加载其独有 operand），每个 operand 只 `LoadNdGmToNzL1` **一次**。
- 【变更】共享 operand 的 L1 tensor 跨多个 `ComputeMM` **持久持有**（前半段加载、前半段某 mm 与后半段某 mm 都读它，最后一个消费者用完才 `FreeTensor`）；仅被单个 mm 使用的 operand 在该 mm 后即可释放。用持久成员 L1 tensor（跨函数调用持有）承载。
- 【不变】各 `ComputeMM` 内的 L1→L0 加载（`LoadNzL1ToZzL0A` / `LoadNzL1ToZnL0B` / 带 `WithTranspose` 的变体）、`Mmad`、`Fixpipe`、`SetAtomicAdd` 参数**完全不变**；不同 mm 用不同读取模式（转置/不转置、作 L0A 或 L0B）复用**同一份 NZ L1 数据**——这正是复用合法的基础（同一份 NZ 数据可被多种 L0 读取模式消费）。
- 【不变】跨核同步（前半段尾 `CrossCoreSetFlag`、后半段首 `CrossCoreWaitFlag`）不变；`TQue` 的 `EnQue`/`DeQue` 仍管理 MTE2(GM→L1)→MTE1(L1→L0) 同步语义，只是 `FreeTensor` 时机延后到阶段末尾。
- 【不变】`Fixpipe` 写出目标（workspace GM 或累加区）、写出字节数、`SetAtomicAdd` 区域不变；本策略只改 L1 加载结构，不改写出。

**expected_speedup_pct：** GM→L1 搬运量与 `LoadData` 标量设置次数随「共享 operand 比例」线性下降（共享比例越高、被复用的 mm 越多收益越大）；典型 `aic_mte2_time` 下降 **30~40%**、`aic_scalar_time` 随 `LoadNdGmToNzL1` 次数下降；**端到端 task duration 收益取决于 cube 是否关键路径**——cube-bound 时显著，vec-bound（`aiv_time > aicore_time`）时端到端收益被 vec 掩盖（但 cube 效率确为真实提升，且为后续 cube-vec 软件流水铺路）。不夸大为固定百分比。

---

## 2. 参数变更表

| parameter | baseline | v1.1 | unit | remark | constraint |
|---|---|---|---|---|---|
| `LoadNdGmToNzL1` 次数（单 tile） | `2 * numMM`（每 mm 加载 A、B） | `numOperands`（每个 operand 一次，去重） | 次 | 共享 operand 只加载一次 | 去重后次数 = 实际不同 GM operand 数 |
| 共享 operand GM→L1 搬运次数 | K（K=使用它的 mm 数） | 1 | 次/operand | 跨 mm 复用 | 见反模式：中途 Free 会让后续 mm 读到被释放数据 |
| L1 tensor 持有范围 | 单 mm 内（用完即 Free） | 跨多个 mm（持久成员，最后消费者后 Free） | — | 持久持有 DeQue tensor | 见反模式：depth=1 时持有期间不得再 AllocTensor 同 que |
| L1 峰值占用 | 单 mm 的 A+B | 阶段内全部需并存 operand 之和 | 字节 | 前半段须同时持全部 operand | 峰值 ≤ L1 容量（ascend-hardware 真实值，禁硬编码） |
| L1→L0 读取模式（各 mm） | 各 mm 自定 | 各 mm 自定（不变） | — | 同一 NZ L1 数据被不同模式读取 | 转置/非转置、L0A/L0B 均接受同一 NZ 输入 |
| MTE2→MTE1 同步 | 每 mm 内 EnQue/DeQue | 集中加载处 EnQue/DeQue，持有期间不再重发 | — | DeQue 后 MTE2 完成、可供 MTE1 读 | TQue 同步语义不变，仅 Free 时机延后 |
| 跨核 flag | 不变 | 不变 | — | 前半段尾 Set / 后半段首 Wait | 本策略不动跨核同步 |
| Fixpipe 写出 | 不变 | 不变 | — | 写出目标/字节/AtomicAdd 区域不变 | 本策略只改加载结构 |

---

## 3. 结构变更模式

抽象结构（不含真实变量名/行号）：把各 matmul 自包含的「GM→L1 加载」剥离，集中到阶段前置；共享 operand 的 L1 tensor 用持久成员跨 mm 持有，各 mm 只做 L1→L0→Mmad→Fixpipe，最后统一释放。

```text
// ========== 前半段（cube stage 1）：集中加载 + 两个 mm 复用 ==========
aL1 = LoadToL1(queA, gmA, offA, ...)          // operand A：mm1 用、mm3 复用 → 持久持有
bL1 = LoadToL1(queB, gmB, offB, ...)          // operand B：mm1 用、mm4 复用 → 持久持有
cL1 = LoadToL1(queC, gmC, offC, ...)          // operand C：仅 mm1 用
dL1 = LoadToL1(queD, gmD, offD, ...)          // operand D：mm2 用、mm3 复用 → 持久持有

ComputeMM1(aL1, cL1)                           // mm1：A@C^T（A 作 L0A、C 作 L0B 转置）
ComputeMM2(aL1, dL1)                           // mm2：A@D^T（A 复用，作 L0A；D 作 L0B 转置）
queC.FreeTensor(cL1)                           // C 仅 mm1 用，mm1 后释放
// aL1 / bL1 / dL1 保留，供后半段 mm3/mm4/mm5 复用
CrossCoreSetFlag<...>(stage1_done_flag)        // 前半段尾同步（不变）

// ========== 后半段（cube stage 2）：加载独有 operand + 复用前半段持有的 ==========
CrossCoreWaitFlag<...>(stage2_ready_flag)      // 等 vec 写完中间 workspace（不变）
eL1 = LoadToL1(queE, gmE_ws, offE, ...)        // operand E：mm3 用、mm4 复用 → 持久
fL1 = LoadToL1(queF, gmF_ws, offF, ...)        // operand F：仅 mm5 用

ComputeMM3(eL1, dL1)                           // mm3：E@D（E 作 L0A；D 复用作 L0B 非转置）
ComputeMM4(eL1, aL1)                           // mm4：E^T@A（E 复用，转置作 L0A；A 复用作 L0B）
ComputeMM5(fL1, bL1)                           // mm5：F^T@B（F 作 L0A 转置；B 复用作 L0B）

// 阶段末统一释放全部 L1
queE.FreeTensor(eL1);  queF.FreeTensor(fL1)
queD.FreeTensor(dL1);  queA.FreeTensor(aL1);  queB.FreeTensor(bL1)
```

**为何不同读取模式可复用同一份 L1 数据**：`LoadNdGmToNzL1` 产出的是 NZ 分形格式的 L1 数据；`LoadNzL1ToZzL0A`、`LoadNzL1ToZnL0B`、以及各自的 `WithTranspose` 变体，**输入都接受 NZ 格式的 L1 tensor**，转置/角色选择由 L1→L0 这一步决定，与 L1 数据本身无关。因此同一份 NZ L1 数据可被「mm_i 作 L0A 不转置」「mm_j 作 L0B 转置」等多种模式分别读取，结果各正确。这是跨 mm 复用在数学/硬件上合法的根本原因。

---

## 4. 反模式

- **pattern**：未核算 L1 峰值容量就同时加载并持有阶段内全部 operand。 **reason**：operand 数量 × 单 operand 大小（如 `BLOCK_M*BLOCK_K*sizeof`）之和可能超过 L1（如 512KB），尤其 depth>1 时。 **metrics**：L1 OOM / 编译期或运行期越界崩溃。
- **pattern**：共享 L1 tensor 在某个中间 mm 之后被 `FreeTensor`，后续复用它的 mm 读已释放 slot。 **reason**：`FreeTensor` 归还 slot，下次 `AllocTensor`（下个 tile）会覆盖；若在同 tile 内提前 Free，后续 mm 读到将被覆盖的数据。 **metrics**：静默数据错位 / 精度 FAIL（首个 tile 可能正常，极隐蔽）。
- **pattern**：`depth=1` 的 L1 TQue 在持有 DeQue tensor 期间，对同一 que 又 `AllocTensor`。 **reason**：depth=1 只有一个 slot，未 Free 时 AllocTensor 会阻塞或覆盖。 **metrics**：死锁或数据覆盖。
- **pattern**：跨「前半段→后半段」持有 L1 tensor，但中间跨核 `WaitFlag` 所在 pipe 与 L1 数据可见性混淆，误以为需要额外同步。 **reason**：跨核 flag 在 FIX/MTE2 pipe，不触碰 cube 本核 L1 物理内容；L1 数据在持有期间无覆盖即不变。 **metrics**：多加冗余同步（损失性能）或漏加必要同步（数据竞争）。
- **pattern**：把 L1→L0 读取模式（转置/角色）当作 operand 属性写死，导致复用时用错模式。 **reason**：同一 operand 在不同 mm 中角色不同（A 矩阵 vs B 矩阵、转置 vs 非转置），读取模式是 mm 级属性而非 operand 级。 **metrics**：矩阵乘维度/转置错配 → 结果错误。
- **pattern**：为追求复用改变 mm 的执行顺序或 Fixpipe 写出布局。 **reason**：本策略只改加载结构，mm 顺序与写出布局涉及下游 workspace 寻址与精度，属另一策略范畴。 **metrics**：workspace 读写错位 / 精度 FAIL。

---

## 5. 硬件约束表

| resource | capacity | baseline_usage | v1.1_usage | constraint |
|---|---|---|---|---|
| L1（cube 侧） | 芯片相关，ascend-hardware 获取（禁硬编码 KB） | 单 mm 的 A+B（峰值小） | 阶段内全部需并存 operand 之和（峰值大） | v1.1 峰值须 ≤ L1 容量；按「同时持有最多 operand」核算 |
| L0A / L0B / L0C | 芯片相关 | 各 mm 内 Alloc/Free | 不变（各 mm 内仍 Alloc/Free） | 本策略不动 L0 生命周期 |
| L1 TQue depth | ≥1 | 1（baseline 常为 1） | 1 即可（跨函数持有 DeQue tensor，无需 depth>1） | depth=1 时持有期间禁再 AllocTensor 同 que |
| MTE2（GM→L1）带宽 | 芯片相关 | `Σ 2*numMM*operandBytes`（含重复） | `Σ numOperands*operandBytes`（去重） | 共享比例越高，MTE2 字节数下降越大 |
| `LoadNdGmToNzL1` 标量开销 | 每 16×16 分形一次地址推导 | `2*numMM` 次 | `numOperands` 次 | 是 `aic_scalar_time` 下降的主要来源 |

---

## 6. 协同建议

- **本策略可独立执行**：只重构 cube 阶段的 L1 加载与持有结构，不依赖组内其他策略状态，不与 vec 侧改动冲突。
- **synergistic_with（可选叠加）**：
  - vec 子核切分策略：vec 与 cube 正交，可同时生效。
  - vec 批量 Cast 循环消除策略：作用于 vec 写回，与本策略（cube 加载）互不干扰。
  - **cube-vec 软件流水**（跨策略）：本策略让 cube 变快（`aicore_time` 下降），是软件流水能产生任务级重叠收益的**前置条件**——若 cube 仍很慢，软件流水无法把 cube 隐藏在 vec 之后。建议先做本策略再做软件流水。
- **conflicts_with**：若 L1 容量不足以同时持有全部共享 operand（峰值超限），须退化为「部分复用」（只复用容量允许的子集）或配合 `AsdopsBuffer` 全量 L1 ping/pong 分区（属更重的 L1 布局重构策略）。

---

## 7. 验证要点

**compile_check**：
- 集中加载的 L1 tensor 为持久成员（跨函数调用持有），编译期可确认生命周期。
- 阶段内同时持有的 operand 总和 ≤ L1 容量（用 ascend-hardware 真实 L1 核算，禁硬编码）。
- 每个 operand 的 `FreeTensor` 时机在「最后一个使用它的 mm」之后；无悬挂 `DeQue` 无 `Free`（slot 泄漏）或提前 `Free`（覆盖）。
- `depth=1` TQue 持有期间无第二次 `AllocTensor`。

**accuracy_check**：
- **必须覆盖 operand 被多个 mm 以不同读取模式（L0A/L0B、转置/非转置）复用的场景**：验证同一份 L1 数据被多种模式读取后，各 mm 结果与 baseline（各自独立加载）逐位一致（数学等价，仅加载次数减少）。
- 覆盖尾块（`actualRows < BLOCK`）shape：复用的 operand 在尾块下行数/列数变化，验证 `LoadNdGmToNzL1` 的 rows 参数与下游 `mExtension`/`Fixpipe mSize` 仍自洽。
- 覆盖共享 operand 跨「前半段→后半段」持有（中间隔跨核同步）的 shape：验证 L1 数据在持有期间未被覆盖、后半段 mm 读到正确数据。
- 多 batch / 多 head shape：验证 operand 偏移随 task 正确推进，复用不串 head/batch。

**performance_check**：
- `aic_mte2_time` 下降（GM→L1 搬运字节数减少，下降幅度 ∝ 共享 operand 比例）。
- `aic_scalar_time` 随 `LoadNdGmToNzL1` 次数下降而下降。
- `aic_mac_time`（真实矩阵乘）**应保持不变**（作为回归对照——本策略不改计算量，只改加载）。
- 端到端 task duration：cube-bound 时显著下降；vec-bound 时可能被掩盖（但 `aicore_time` 下降可观测，且为软件流水铺路）。

## 检索卡（短卡）

动作：将多个matmul的共享操作数改为在Cube侧L1中跨matmul复用。
适用：同一Cube计算阶段含多个matmul，且存在被多个matmul共享的操作数。
范围：Cube侧单个多matmul计算阶段。
检索词：Cube、多matmul、共享操作数、L1复用。
机会：多个matmul重复使用相同操作数。
