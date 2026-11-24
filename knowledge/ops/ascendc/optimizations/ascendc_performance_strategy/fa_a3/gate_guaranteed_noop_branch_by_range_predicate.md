---
type: Optimization
title: 谓词门控快速路径（外层一次判定恒空分支/全局谓词，索引区间推导或有序数据探针）
description: 在内层循环外计算循环不变量 feasible，用它门控原保护分支。
tags:
- task.optimization
- topic.attention
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/04-gate-guaranteed-noop-branch-by-range-predicate.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：谓词门控快速路径（外层一次判定恒空分支/全局谓词，索引区间推导或有序数据探针）

> **单一优化点：** 在 AscendC kernel 中，任何一段"为了兜底某个边界情形而**每次迭代/每行都执行**"的保护代码（典型：逐元素/逐行 `GetValue` + 判断 + 一个跨管线 `PipeBarrier`），或一段"先 O(N) 扫描决定全局性质、再据此分支处理"的逻辑，如果其触发条件可在外层**一次**判定，就把判定上提为外层谓词并门控整段——不可能命中时**整段跳过**，省掉其 scalar 工作与跨管线 barrier。谓词来源有两种（§3 变体 A / §3B 变体 B）：
>
> - **变体 A（区间极值推导，本文件主体）：** 边界情形只在某个**索引表达式**落入特定区间时才可能发生，谓词由外层索引纯计算得出，不读任何数据。
> - **变体 B（有序数据边界探针，原 06-ordered-invariant-o1-fast-path 已并入）：** 数据满足**已知有序不变量**（升序/降序/单调，极值或哨兵位于已知端），用探针一个边界元素（通常为末元素）把 O(N) 全局 ∃/∀ 谓词塌缩为 O(1)。适用于"循环对一段连续元数据/控制数据（索引、掩码、长度、标志位）的处理依赖全局谓词"的模式。
>
> **算子无关性：** 本策略适用于**所有**管线（Vector `MTE2/MTE3/V`、Cube `MTE1/M`）下、形如"`for i: if 可能触发边界 E: <逐元素兜底> + barrier`"的保护分支，以及任何"先扫描一段范围决定全局性质、再据此分支处理"的模式。典型边界 `E`：因果/下三角 mask 下"整行被全 mask（`rowMax==-inf`）"、padding 行保护、OOB clamp（列范围是否越界）、"可能含 NaN/inf 的 flush"、reduction"全零早退"、"是否存在 -1/无效元""是否全部有效""是否存在 0 长度"等。

本策略只改"保护分支/谓词判定的执行条件"：把内层恒定可判的触发条件**上提**为一个外层谓词，false 则跳过保护体（变体 A），或塌缩 O(N) 谓词扫描为 O(1) 探针 + 快/慢路径分流（变体 B）。不改保护体本身的数学、不改 mask/scale 语义、不改数据布局、不改 buffer 深度、不删任何非该保护所需的同步、不引入新算法。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

很多 kernel 为了正确性，在内层循环里挂一段"兜底"保护：每个元素/每行都查一次"是否命中某个罕见边界情形"，命中才做修正，否则空转。保护体通常含 `GetValue`（从 UB 读标量）、逐元素 `SetValue`、以及一条**跨管线 `PipeBarrier`**（因为保护体与主计算跨管线，需要同步）：

```text
for i in rows_in_tile:                 # 内层：每行都跑保护
    if 可能触发边界 E(i):              # 边界 E 是某索引表达式的函数
        <逐元素兜底修正>               # GetValue + SetValue ...
        PipeBarrier<PIPE_V>()          # 跨管线同步（每次都挂）
```

当 `E(i)` 在**本 tile/chunk 内对所有 `i` 都不可能成立**时，整段保护是**恒空（dead）**的，但其 `GetValue` 循环 + `PipeBarrier` 仍逐行执行，成为纯 scalar + 同步开销。tile 数多、行数大时（长序列、多 chunk），该开销随 `(tile 数 × 行数)` 线性堆叠。

典型症状：profiling 显示 Vector `aiv_scalar_time`（`GetValue`/分支）或 `aiv_vector_time` 占比偏高，且该段无有效计算产出；逐 tile 剖析可见一条固定的小开销条与一条 `PIPE_V` barrier。

### 1.2 本策略利用的机制

| 机制 | 利用方式 |
|---|---|
| 索引表达式的单调性 | 边界 `E(i)` 依赖的索引表达式（如 `globalI = qRowStart + base + i`、`col = colStart + j`）在 tile 内随 `i/j` 单调，故"tile 内是否**存在**命中 `E` 的迭代"等价于"该表达式在 tile 内的**极值**是否落入 `E` 的触发区间" |
| 区间可行性谓词 | 极值由外层索引（`qRowStart / colStart / s2Start / causalOffset …`）一次性算出，与内层 `i/j` 无关 → 谓词是**循环不变量**，可提到循环外 |
| 跨管线同步消除 | 保护体是唯一挂载该 `PipeBarrier` 的位置时，跳过保护体即一并省掉这条 barrier；保护体不是该 barrier 唯一来源时，barrier 保留（见 §6.2） |
| 分支预测 / scalar 单元 | tile 内恒 false 的分支整段跳过，省掉 `tile行数` 次 scalar 查询 |

核心改动——把内层 `if E(i)` 改写为外层 `if feasible(E over tile)`：

```text
# 基线
for i in rows_in_tile:
    if E(globalExpr(i)):               # 每行查
        guardBody(...)
        PipeBarrier<PIPE_V>()

# 改写后
feasible = extremumOf(globalExpr, tile) 落入 E 的触发区间   # 外层算一次（循环不变）
if (feasible) {                         # 整 tile 只判一次
    for i in rows_in_tile:
        if E(globalExpr(i)): guardBody(...)
        PipeBarrier<PIPE_V>()
}
```

`feasible` 为 `false` 时整段跳过；为 `true` 时与基线**逐位等价**（保护体原样执行）。

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 保护形态 | 存在内层逐元素/逐行执行的保护分支，其触发条件 `E` 可表达为"某索引表达式 `f(i,...)` 落入触发区间 `[lo,hi)`（或 `< t` / `> t`）" |
| `f` 单调可极值 | `f` 在 tile 内对迭代变量 `i/j` **单调**，极值取 tile 内迭代变量的首/末（`f_min`/`f_max` 由外层索引一次性算出） |
| 可行性可判 | 能由 `f_min`/`f_max` 判定"tile 内是否存在命中 `E` 的迭代"（区间相交/包含判定） |
| 保护体无副作用泄漏 | 保护体只对**本 tile 数据**做幂等/局部修正（写本 tile 的 UB/L1，或设标量状态）；不写跨 tile 共享、被别处依赖的状态（否则跳过会丢更新，见 §6 陷阱 2） |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- 触发区间 `E` 在大量 tile 内恒不命中（如 causal 下 `causalOffset` 大、全 chunk `jThresh≥0`；或 tile 列范围恒在界内）。
- 保护体含跨管线 `PipeBarrier`，且该 barrier 仅由此保护挂载（一并省 barrier 收益最大）。
- tile 数 / 行数大（长序列、多 chunk），开销随规模堆叠。

不适用或需先重构：

- `E` 依赖**数据**而非索引（如"某元素是否 NaN/inf"、"某 score 是否恰好 0"）——索引区间分析无法判定，**不可**用本策略（除非有生产者侧的有限性 flag，见 §3.3）。
- 保护体的 `PipeBarrier` 还服务于本 tile 内**其他**跨管线同步（如等待另一条 DMA 完成）——barrier 不能随保护体一起跳过，须保留（见 §6.2 / §6 陷阱 3）。
- 保护体写跨 tile 共享状态（如全局 reduce 标志、跨核 flag）——跳过会丢更新。
- `feasible` 无法被外层索引静态表达（依赖内层 `i` 的非线性组合）——需先重构索引或退回基线。

---

## 3. 区间谓词的构造

### 3.1 通用三步

```text
# 1) 写出 E 的索引充要条件：E(i) ⟺ f(i) ∈ TRIGGER  （TRIGGER = [lo,hi) / (-∞,t) / (t,+∞)）
# 2) 求 f 在 tile 内的极值（i 单调时取首/末）：
f_min = f(i = i_first)        # 通常 i_first = 0（最小行/列）
f_max = f(i = i_last)
# 3) tile 内存在命中 ⟺ [f_min, f_max] 与 TRIGGER 相交：
feasible = intersects([f_min, f_max], TRIGGER)
```

`feasible` 仅由外层索引（`qRowStart/colStart/s2Start/causalOffset/...`）决定，是循环不变量。

### 3.2 典型场景：causal mask 下的"整行全 mask"保护

边界 `E`：softmax 后某行 `rowMax == −inf`（整行被全 mask → 该行须强制为 0，否则 `exp(−inf)=0` 使该行输出 0 但状态 `rowSum=0` 在后续 merge/输出里产生 NaN/垃圾）。

- 充要条件：`rowMax == −inf` ⟺ 该行**所有** KV 列被因果 mask 为 `−inf` ⟺ 该行 causal 阈值 `jThresh = globalI + causalOffset − s2Start < 0`（无任何合法列）。
- `f(i) = jThresh(i) = globalI(i) + causalOffset − s2Start`，对行 `i` 单调（`globalI` 随 `i` 增）。
- tile 内最小行给出 `jThresh` 极小值 → `feasible ⟺ min_jThresh < 0`。

```text
causalOffset = KV_len - Q_len                  # query 长度远小于 KV 长度时很大（>0）
min_jThresh = <tile 内最小 globalI> + causalOffset - s2Start
feasible = (min_jThresh < 0)                   # false ⇒ 整 chunk 无全 mask 行 ⇒ 跳过保护分支
```

当 `causalOffset` 很大（本 tile 的所有 query 位置都"新于"全部 KV 位置）时，整 chunk `min_jThresh ≥ 0`，`feasible=false`，逐行 `GetValue(rowMax)` 循环 + `PipeBarrier<PIPE_V>` 整段跳过。

### 3.3 其他典型场景（泛化）

| 边界 `E` | 索引条件 | 极值谓词 `feasible` |
|---|---|---|
| padding 行（整行越界） | `globalRow ≥ validRows` | `tile 末行 globalRow < validRows` 时 `false` |
| OOB 列 clamp 必要性 | `col ≥ validCols` | `tile 末列 col < validCols` 时 `false`（全在界内，clamp 跳过） |
| 上三角/反向 causal 全 mask | `globalI + off - s2Start < 0`（同上，方向取决于 mask 语义） | 同 §3.2 |
| 有限性 flush（生产者保证有限） | 生产者侧 `allFinite` flag | `allFinite==true` 时 `false`（数据驱动，见 §2 不适用项的例外） |

> **数据驱动边界的例外：** 若 `E` 依赖数据但存在**生产者侧静态 flag**（如上游 cast 保证无 inf），可用该 flag 当 `feasible`；否则不可套用本策略。数据驱动的全局谓词若数据满足有序不变量，可走变体 B（§3B）。

### 3B 变体 B：有序不变量驱动的 O(1) 边界探针 + 快/慢路径

当循环对一段连续元数据/控制数据（索引、掩码、长度、标志位等）的处理依赖一个**全局谓词**（如"是否存在 -1/无效元""是否全部有效""是否存在 0 长度"）时，O(N) 谓词扫描本身也是被优化的对象。

低效基线（两种模式）：

```text
# 模式 A：仅判定（如"是否存在无效元"）
has = false
for i in 0 .. N:
    if pred(data[i]): has = true; break        # O(N) 标量扫描

# 模式 B：判定 + 据此分支处理（如"全有效⇒统一处理，否则逐元素条件处理"）
for i in 0 .. N:
    if elemNeedsSpecial(data[i]):
        <特殊处理（清零/掩码/分支）>             # 每元素一次条件 + 特殊工作
```

改写（探针 + 快/慢路径）：

```text
# 判定：O(N) → O(1)
hasSpecial = (data[N-1] == sentinel)            # 升序、sentinel 在尾 ⇒ 末元素探针

# 处理：快/慢路径
if !hasSpecial:                                 # 快路径（主用例）
    <统一处理所有元素（无逐元素条件/特殊工作）>    # 特殊元用安全兜底（如 clamp）+ 下游忽略
else:                                           # 慢路径（谓词成立）
    <通用 O(N) 处理，任意顺序正确>                # 清零/掩码/逐元素条件，与原逻辑一致
```

**不变量是输入契约（正确性核心）：**

- 有序不变量（如"升序、-1 在尾"）**必须由数据生产方/上游/测试桩保证**，不是本算法自己建立的。
- 必须在代码注释与契约文档中**显式声明**该不变量及其来源；若上游可能破坏不变量，必须先在入口校验或排序，否则快路径不安全（陷阱 6）。
- **探针可靠性必须可证明**：哨兵是**极值**、且不变量把所有哨兵**聚到被探针端**。例：升序 + 哨兵为最小值且全在尾 → `last >= 0 ⇒ 整段无 -1` ✓；反例：若 -1 可出现在任意位置（非尾），`last >= 0 ⇏ 整段无 -1` ⇒ 探针不可靠，不得使用。
- **快/慢路径语义等价 + 下游耦合**：两路径必须产生相同可观测结果；若快路径对"潜在特殊元"采用安全兜底（如无效索引 `clamp(min=0)` 取第 0 行），必须保证兜底值无害（下游按谓词 mask/忽略这些元），**且**下游 mask 的正确性不反向依赖被本快路径影响的判定（避免循环依赖，陷阱 7）。
- 边界：空范围（N==0）短路（不探针、不处理，或按语义给默认谓词值）；单元素范围探针即该元素。

变体 B 的适用条件（须同时满足）：循环依赖一个 ∃/∀ 全局性质（非逐元素独立判定）；数据满足已知有序不变量且为输入契约；主用例谓词"不成立"（无特殊元）高频（否则快路径命中率低，见陷阱 8）；存在任意顺序都正确的通用慢路径回退。优先适用：N 较大且数据天然有序（已排序的 TopK 索引、单调长度数组、连续掩码段）、主用例大量"全有效"。

---

## 4. 实施步骤

### 4.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| kernel 内挂保护的内层循环外 | 新增 `feasible` 计算（外层索引，循环不变量）；把原"内层 `if E(i): guardBody; barrier`"整体包进 `if (feasible) { ... }` |
| 保护体 `guardBody` | **不改**（数学/写法/同步原样） |
| `PipeBarrier` | 仅当该 barrier **仅**由保护体挂载时随保护体一起进 `if`；否则保留在 `if` 外（见 §6.2） |
| Host tiling / 数据布局 / buffer 深度 / 其他同步 | **不改** |

### 4.2 通用改写

```text
# 基线
ApplyGuard(tile, ...) {
    for (i = 0; i < rowsInTile; ++i) {
        if (E(globalExpr(i))) {
            <guardBody>                 // 逐行 GetValue + SetValue
        }
    }
    PipeBarrier<PIPE_V>();              // 该 barrier 仅由本保护挂载
}

# 改写后
ApplyGuard(tile, ...) {
    fMin = f(i_first), fMax = f(i_last);                 // 外层索引算极值
    bool feasible = intersects([fMin, fMax], TRIGGER);    // 循环不变
    if (feasible) {                                       // 整 tile 只判一次
        for (i = 0; i < rowsInTile; ++i) {
            if (E(globalExpr(i))) { <guardBody> }         // 与基线逐位等价
        }
        PipeBarrier<PIPE_V>();
    }
    // feasible==false ⇒ 保护体 + barrier 整段跳过
}
```

---

## 5. 正确性红线

### 5.1 可行性谓词的方向（sound over-approximation）

`feasible` 必须是**可靠上近似**：

- `feasible=false` ⟹ `E` 在 tile 内**确实**对所有迭代都不可能发生（跳过安全）。
- `feasible=true` 但 `E` 实际不发生 ⟹ 保护体空跑（**安全，仅慢**）。
- `feasible=false` 但 `E` 实际可能发生 ⟹ **BUG**（漏保护，结果错误）。

故极值/区间相交判定必须取**保守方向**：拿不准时令 `feasible=true`（保留保护），绝不为求性能令其为 `false`。

### 5.2 极值必须覆盖 tile 内**全部**迭代

`f_min/f_max` 须取 tile 内迭代变量的真实首/末，不可漏掉尾块、子 chunk、或未满块的情形（见 §6 陷阱 1）。多 chunk 时极值随 `chunkRow` 变化，`feasible` 须按 chunk 重算（不可外提成"整 task 一次"）。

### 5.3 保护体的副作用范围

保护体只可写**本 tile 数据 / 本行局部状态**。若它写跨 tile 共享状态（全局 `rowSum`、跨核 flag、workspace 累加器），跳过会丢更新（§6 陷阱 2）——此时**不可**门控，或须证明该状态在 `feasible=false` 时本就不需要更新。

### 5.4 数值正确性

不改保护体数学、不改 mask/scale、不改累加顺序与输出 dtype/布局。`feasible=true` 时保护体逐位等价于基线；`feasible=false` 时该 tile 本就无 `E` 命中，跳过等价。

---

## 6. 已知陷阱

### 陷阱 1：极值漏算尾块/子 chunk，误判 feasible=false

问题：`f_min` 取了"主块首行"，漏掉子 chunk（`chunkRow>0`）或多 chunk 的行，使 `feasible` 偏小为 false。
触发：tile 放大后单次处理范围超过一个子 chunk（⇒ 多 chunk）或行尾块。
症状：本该保护的行被跳过，mismatch 集中在对应行（如 causal 全 mask 行未被强制 P=0 → 输出 NaN/垃圾）。
修复：极值按 tile 内真实首/末行算，多 chunk 时 `feasible` 含 `chunkRow` 逐 chunk 重算（见 §5.2）。

### 陷阱 2：保护体写跨 tile 共享状态，跳过丢更新

问题：保护体除修正本 tile 外，还写全局 `rowSum`/跨核 flag/workspace 累加器；`feasible=false` 跳过后该更新丢失。
症状：下游依赖该状态的计算结果错误（如 softmax merge、输出累加）。
修复：确认保护体只写本 tile 局部状态（§5.3）；写共享状态的分支**不可**门控。

### 陷阱 3：误把服务多处的 `PipeBarrier` 随保护体一起跳过

问题：保护体的 `PipeBarrier<PIPE_V>` 同时等待本 tile 另一条跨管线 DMA 完成；跳过保护体时把 barrier 也跳了。
症状：后续读到未完成的跨管线数据，随机 mismatch / 数值抖动。
修复：barrier 是否可跳取决于它是否**仅**由保护体挂载（§4.1）。不确定时 barrier 保留在 `if` 外。

### 陷阱 4：把数据驱动的 `E` 当索引驱动来门控

问题：`E` 依赖数据（元素是否 NaN/inf、score 是否恰为某值），却用索引区间谓词门控。
症状：索引谓词判 `false` 跳过，但数据里实际命中 `E` → 漏保护，结果错误。
修复：仅当 `E` 是**纯索引条件**（或存在可靠生产者 flag，§3.3）才用本策略；数据驱动者保留逐元素保护。

### 陷阱 5：误把"未测到收益"当策略失效

问题：某 case 保护体本就轻（无 barrier 或行数少），门控后整体耗时持平，误判失效而回退。
诊断：剖该 tile 的 `aiv_scalar`/`aiv_vector` 是否下降、`PIPE_V` barrier 数是否减少；下降即对保护体生效。整体耗时取决于该保护占总开销比例（"小但确定"的下降即属此类收益）。

### 陷阱 6（变体 B）：不变量未保证/未声明，快路径静默出错

问题：上游数据实际无序（或 -1 不在尾），探针误判，快路径处理错。
症状：特定输入 mismatch，常呈"主用例对、边角用例错"。
修复：不变量作为输入契约显式声明；不可保证时入口校验/排序或禁用快路径（只留慢路径）。

### 陷阱 7（变体 B）：多处探针判定不一致（循环依赖）

问题：A 处快路径依赖下游 B 的 mask；B 的 mask 又依赖另一探针；两探针基于不同假定或其一出错。
症状：谓词与下游 mask 失配，特殊元未被 mask。
修复：所有相关探针基于同一不变量、一致判定；或集中到单一谓词源。另注意慢路径"仅处理有效元"时累加器/buffer 单缓冲复用会残留上轮数据——慢路径批首须清零未用槽位。

### 陷阱 8（变体 B）：主用例谓词频繁成立，快路径反成负担

问题：特殊元常在，快路径命中率低，额外分支探针反增开销。
诊断：profiling 显示快路径几乎不命中、`aiv_scalar` 未下降。
修复：确认主用例偏向（谓词"不成立"高频）后再用；否则不用变体 B。

---

## 7. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 保护分支 | 哪段代码是"逐元素/逐行兜底"？触发边界 `E` 是什么 |
| `E` 性质 | `E` 是**纯索引条件**（可由 `f(i)∈TRIGGER` 表达）还是数据驱动？数据驱动者不适用（除非有序不变量成立走变体 B） |
| 索引表达式 | `f(i)` 是什么？在 tile 内是否单调？极值 `f_min/f_max` 如何由外层索引算出 |
| 触发区间 | `TRIGGER` 是 `[lo,hi)` / `<t` / `>t`？`feasible` 的相交判定式 |
| 副作用范围 | 保护体是否只写本 tile 局部状态？有无跨 tile 共享写（§6 陷阱 2） |
| barrier 归属 | 保护体的 `PipeBarrier` 是否**仅**由保护体挂载？能否随跳过（§6 陷阱 3） |
| 极值完备性 | 极值是否覆盖 tile 内全部迭代（尾块、多 chunk、`chunkRow`）（§6 陷阱 1） |
| 收益预期 | 该保护在目标 case 占总开销比例？剖 `aiv_scalar/vector` 与 barrier 数 |
| 基线可重复 | 修改前 build/精度/性能基线值 |
| 变体 B（如适用） | 哪个 ∃/∀ 全局谓词、原 O(N) 扫描在哪；有序不变量是什么、由谁保证（输入契约来源）；探针"边界元素 ⇒ 整段谓词"的推理（哨兵极值 + 聚端）；快路径省掉哪些工作、潜在特殊元的兜底与下游忽略；下游是否有依赖同一谓词的 mask/判定、多处探针是否一致；N==0/单元素/哨兵在边界的处理 |

任一项无法回答，不实施本策略。

---

## 8. 禁止事项与回退条件

禁止：

- 为求性能令 `feasible=false`（破坏 §5.1 的上近似方向）。
- 把数据驱动的 `E` 当索引驱动门控（陷阱 4）。
- 漏算尾块/子 chunk 的极值（陷阱 1）。
- 跳过写跨 tile 共享状态的保护分支（陷阱 2）。
- 把服务多处同步的 `PipeBarrier` 随保护体跳过（陷阱 3）。
- 同一轮混入 mask 数学、buffer 深度、数据布局等改动。

回退或缩小策略的条件：

- 精度失败且无法证明 `feasible` 是可靠上近似 → 整体退回基线。
- 保护体含跨 tile 共享写或共用 barrier，无法安全跳过 → 不门控该分支。
- 剖析显示保护体开销可忽略（无 barrier、行数少）→ 收益不显著，可不实施（陷阱 5）。

---

## 9. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>            # 编译算子
bash <build> --soc=<soc> --op=<op> --wheel    # 编译 pta
source <set_env>
pytest <op>/test/test_<op>.py                 # 精度
pytest <op>/test/test_<op>_perf.py            # 性能（生成 profiling）
```

精度：与基线一致（沿用算子既有 `atol/rtol`）。**必须覆盖 `feasible=true`（保护体仍执行）与 `feasible=false`（整段跳过）两类 case**——前者验证逐位等价，后者验证跳过安全。边界：多 chunk、尾块、`causalOffset` 跨正负、不同 dtype。**变体 B 额外必须覆盖谓词成立与不成立两类用例**——快路径（无特殊元）与慢路径（有特殊元）都要测；含空范围、单元素、哨兵在边界、不变量边界；慢路径对任意顺序输入都应正确。

性能（**必须用 profiling 归因**）：

- 目标 case（`feasible=false` 主导）整体 `Task Duration` 下降，Vector `aiv_scalar`/`aiv_vector` 与 `PIPE_V` barrier 数下降。
- `feasible=true` 主导的 case 不劣化（保护体仍执行，门控仅多一次谓词判断，开销可忽略）。
- 变体 B：谓词判定所在 scalar/扫描时间下降（O(N) 扫描变 O(1) 探针、跳过逐元素条件/特殊工作）；主用例（谓词不成立）整体不劣化且该扫描在关键路径时下降；慢路径用例与基线持平（通用回退不劣化）。边界 shape：全有效（快）、含无效/特殊元（慢）、全无效、空范围、单元素、不同 dtype。

性能结论必须写清基线与触发条件：

```text
本策略收益相对"每次迭代都跑保护体 + barrier"基线；判据是 feasible=false 时保护体整段跳过
带来的 scalar/barrier 下降。收益大小取决于该保护在目标 case 的占比；"小而确定"的下降
即视为对该保护生效，不应误判为失效（§6 陷阱 5）。
```

## 检索卡（短卡）

动作：在内层循环外计算循环不变量 feasible，用它门控原保护分支。
适用：存在内层逐元素或逐行执行的保护分支。
限制：feasible 必须是可靠上近似，不能漏掉可能触发保护的情形。
范围：AscendC kernel 的内层逐元素或逐行保护路径
检索词：区间可行性谓词、feasible、索引表达式、单调性、保护分支
机会：每元素或每行检查罕见边界，未命中时保护代码空转。
