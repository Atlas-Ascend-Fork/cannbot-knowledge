---
type: Optimization
title: 容量驱动的向量后处理行块合并
description: 将向量后处理的固定小逐行块改为容量驱动的行块合并
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/05-vec-row-chunk-coalescing.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：容量驱动的向量后处理行块合并

> **单一优化点：** 对已经完成矩阵输出后的向量后处理阶段，将固定很小的逐行 chunk 改为按向量队列容量、元素宽度、广播对齐约束和 UB 安全预算计算出的最大安全行块，以减少热点循环次数、GM 搬运启动、广播启动、队列交互和同步等待。

本策略不改变矩阵分块、L1 驻留、reduce 轴块大小、跨核任务划分、GM workspace 语义或逐行状态的存放位置。它也不是"状态 GM 往返消除"或"primitive 状态直写最终缓存"的重复；本策略只处理 **同一向量后处理公式在过小行块上重复执行** 的调度开销。

---

## 0. 范围声明

保持不变：

- 数学公式、在线更新顺序、归一化语义和最终输出布局不变。
- 矩阵计算阶段、L0/L1 微块尺寸、reduce 分块和大块驻留策略不变。
- 已有逐行状态缓存的位置、生命周期和 slot 语义不变。
- 需要写回 GM 的中间累加或最终输出语义不变。
- 核间任务划分和跨核同步协议不变。

允许的最小改动：

- 将向量后处理阶段的行 chunk 从固定小常量改为运行期/tiling 期计算值。
- 让 chunk 行数尽量填满已有向量输入/输出队列容量，同时满足广播 primitive 的行对齐要求和 UB 安全预算。
- 复用已有向量 scratch 区作为广播展开缓冲，或按新 chunk 尺寸调整临时缓冲容量。
- 必要时调整向量队列单槽容量或深度，但只服务于本阶段的行块合并。

不属于本策略：

- 不放大任何 L1 大块，不新增 reduce 轴二级分块。
- 不迁移逐行状态的 GM/片上位置。
- 不把 primitive 状态输出改绑到其他缓存切片。
- 不改变 workspace 总体规划作为主要收益来源。
- 不同时重写矩阵阶段、分核策略或 host 入口。

---

## 1. 性能问题模式

基础形态：

1. 一个向量后处理阶段按很小固定行数处理矩阵输出。
2. 每个小 chunk 都重复执行：
   - 从 GM 或 workspace 读取当前输出块。
   - 可选读取上一轮累加块。
   - 读取逐行状态并广播到整行。
   - 对整块数据做缩放、累加、归一化或 cast。
   - 写回中间累加或最终输出。
3. 每个 chunk 的数据量较小，但启动次数很多。

这种路径的问题：

- 总字节数不一定大，但 GM 搬运、广播、vector primitive 和队列入出队的启动次数过多。
- 每个 chunk 都要重复计算 row offset、state offset、尾块判断和 slot 索引。
- 过小 chunk 会放大 pipe barrier、MTE/V 依赖和队列调度的固定成本。
- 广播缓冲按固定小块配置，无法利用可用向量队列容量。

优化目标：

- 在不改变语义的前提下，让单次向量后处理覆盖更多连续行。
- 将 `row_chunks_per_task` 降到接近容量和 UB 预算允许的最小值。
- 保持每个 chunk 的起点和行数满足广播/状态读取对齐。
- 对尾块做显式处理，避免 padding 参与语义。

---

## 2. 适用条件

必须同时满足：

| 条件 | 要求 |
|---|---|
| 行间独立 | 后处理公式对每一行独立，合并多行不会改变行间顺序语义 |
| 行连续 | 当前阶段可以一次处理连续多行，GM/workspace 和状态缓存索引可连续推进 |
| 状态兼容 | 逐行状态读取仍使用同一 slot 和 row offset，只是每次读取更多行 |
| 容量足够 | 输入块、可选上一轮块、输出块、广播缓冲和 scratch 总量不超过向量 UB 预算 |
| 广播对齐 | chunk 行数和起点满足状态广播 primitive 的行粒度要求 |
| 尾块可控 | 最后一个 chunk 的有效行数明确，padding 不被写入最终语义 |

优先场景：

- 后处理阶段包含逐行状态广播、行缩放、行除法、累加或 cast。
- 当前行 chunk 远小于向量队列可容纳的最大行数。
- 每行宽度固定且不大，能够一次容纳几十行或更多行。
- profiling 或静态计数显示该阶段 chunk 数量多、MTE/V 启动和队列操作占比可见。

不适合：

- 行之间存在前后依赖，必须逐行或小组顺序更新。
- 合并行后会超过向量队列、scratch 或广播缓冲容量。
- 广播 primitive 要求的行对齐会导致大量 padding 或更小 chunk。
- 当前瓶颈明确在矩阵计算或大块搬运，向量后处理调度成本占比很低。
- 为了合并行必须新增额外 GM 往返或改变状态缓存布局。

---

## 3. 收益判定模型

实现前先估算新旧 chunk 数和固定开销减少量。

旧 chunk 行数 = 固定小行数常量（如 8）。
新 chunk 行数 = choose_chunk_rows（见第4节），受容量、广播对齐和 UB 预算约束。

旧 chunk 数 = ceil_div(rows_per_worker, old_chunk_rows)
新 chunk 数 = ceil_div(rows_per_worker, new_chunk_rows)

removed_chunk_launches = old_chunks - new_chunks

保守收益模型：

```
saved_cost = removed_chunk_launches * (
    data_copy_launch_cost
    + broadcast_launch_cost
    + vector_launch_cost
    + queue_control_cost
    + barrier_cost
)

added_cost = (
    larger_buffer_pressure_cost
    + possible_lower_queue_overlap_cost
    + tail_handling_cost
)

should_implement = (
    new_chunk_rows > old_chunk_rows
    and new_chunks <= old_chunks * 0.75
    and saved_cost > added_cost * 1.5
)
```

进入实现的硬门槛：

- 新 chunk 行数至少是旧行数的 2 倍，或 chunk 数减少至少 25%。
- 新单槽容量和 scratch 总占用不超过向量 UB 安全预算（见 4a 节）。
- 不新增 GM 读写，不改变矩阵阶段等待关系。
- 预期端到端收益超过测量噪声，建议以 `>= 1%` 作为保留门槛。

若只能减少极少数 chunk，或需要显著增加 UB 占用导致队列深度下降，应判为不适用。

---

## 4. Chunk 选择规则

计算最大安全 chunk 行数，需同时满足以下约束：

1. **行间容量约束**: chunk ≤ vec_buffer_bytes / (row_width × dtype_bytes)
2. **广播对齐约束**: chunk 是 broadcast_align_rows 的整数倍
3. **UB 容量约束**: chunk 导致的总 UB 占用不超过硬件限制（见 4a 节）

取以上约束的最小值，对齐到 broadcast_align_rows，不超过 rows_per_worker。

```python
def choose_chunk_rows(
    rows_per_worker, row_width, dtype_bytes,
    vec_buffer_bytes, scratch_bytes,
    broadcast_align_rows, ub_bytes,        # ub_bytes: 可用 UB 安全预算
    per_row_ub_cost,                       # 每行新增的 UB 字节成本（见 4a.2）
    max_rows_per_chunk=None):
  row_bytes = row_width * dtype_bytes
  capacity_rows = vec_buffer_bytes // row_bytes
  ub_safe_rows = ub_bytes // per_row_ub_cost
  chunk = min(capacity_rows, ub_safe_rows)
  chunk = max(chunk, broadcast_align_rows)
  chunk = AlignDown(chunk, broadcast_align_rows)
  if chunk == 0: chunk = broadcast_align_rows
  if max_rows_per_chunk is not None:
    chunk = min(chunk, max_rows_per_chunk)
  return min(chunk, rows_per_worker)
```

补充规则：

- `row_width` 使用实际参与 vector 计算的对齐后列宽；最终写出仍按真实有效列处理。
- 若同一 chunk 需要同时持有当前块、上一轮块和输出块，容量计算必须按并发驻留的最大组合估算。
- 广播缓冲大小按 `align_up(chunk_rows, broadcast_align_rows)` 计算。
- 若最后一个 chunk 不满足对齐，允许内部按对齐容量分配，但只对有效行读写。
- 不要为了追求最大 chunk 行数而把队列深度降到无法覆盖 MTE/V 交叠；容量和 overlap 要一起评估。

### 4a. UB 容量预算

> **本节是关键补充。** 策略第4节的 `choose_chunk_rows` 函数若只考虑了容量和广播对齐，会忽略 UB 硬约束，导致理论最优 chunk 值在实际硬件上不可行。本节给出 UB 约束的计算方法和捷径。

#### 4a.1 硬件参考值

Ascend 910B AIV UB ≈ **192 KB**。实际可用容量需减去运行时开销（约 4-8 KB），安全预算建议取 190 KB。

> 注意：不同 Ascend 芯片版本 UB 容量不同。实施前应确认目标硬件的 UB 规格。若 UB ≥ 1.4 MB（如 910B2），本节约束可放宽，chunk 行数可接近 rows_per_worker。

#### 4a.2 Buffer 增长列表

chunk 增大时，以下 buffer 占用增长。计算 `per_row_ub_cost` 时需逐一累加：

| Buffer 类别 | 共享类型 | 每行增长量 | 增长条件 |
|---|---|---|---|
| 输入队列 slot × queue_depth | Vec1/Vec2 共享 | max(vec1_chunk_bytes_per_slot, chunk×row_bytes_float) × depth | chunk×row_bytes_float > vec1_chunk_bytes_per_slot 时才增长 |
| 输出队列 slot × queue_depth | Vec1/Vec2 共享 | max(vec1_chunk_bytes_per_slot_half, chunk×row_bytes_half, chunk×row_bytes_float) × depth | chunk×row_bytes_float > vec1_chunk_bytes_per_slot_half 时才增长 |
| 前轮累加 TBuf | 专用 | row_bytes_float × chunk_rows | 总是增长 |
| 广播 TBuf | 专用 | AlignUp(chunk_rows, broadcast_align) × broadcast_align × sizeof(float) | 总是增长 |

其中：
- `row_bytes_float = column_align × sizeof(float)`
- `row_bytes_half = column_align × sizeof(QType)`
- `vec1_chunk_bytes_per_slot` = Vec1 单次处理的字节数（与 Vec1 chunk 行数和矩阵块大小相关）
- `vec1_chunk_bytes_per_slot_half` = Vec1 单次处理的 half 字节数

**per_row_ub_cost 的简化估算**:

保守计算（假设共享 slot 不增长）：
```
per_row_ub_cost_conservative = row_bytes_float + broadcast_align × sizeof(float)
```

完整计算（考虑共享 slot 可能增长）：
```
per_row_ub_cost_full = per_row_ub_cost_conservative
    + (shared_slot_growth_if_vec2_exceeds_vec1 × queue_depth)
```

#### 4a.3 保守上限捷径

> **这是实施中最实用的 shortcut。** 当不希望 Vec1/Vec2 共享的队列 slot 增大时（最常见的 UB 溢出来源），可以直接计算一个保守上限：

```
conservative_chunk_rows = vec1_chunk_bytes_per_slot_half / row_bytes_float
```

对齐到 broadcast_align_rows 后使用。

**直觉解释**: 输出队列 slot 需同时容纳 Vec1 的 half 输出和 Vec2 的 float 输出。当 chunk × row_bytes_float ≤ vec1_chunk_bytes_per_slot_half 时，slot 大小不变，UB 不增长。超过此值时 slot 增大，是 UB 溢出的最常见触发点。

#### 4a.4 UB 溢出判定

```
total_ub = sum(all_buffer_allocations)  ≤  ub_limit (≈190KB for 910B)
```

计算步骤：
1. 列出所有 buffer 分配（Vec 侧的 TQue × depth × slot_size + TBuf × size）
2. 求和
3. 与 ub_limit 比较

若 total_ub > ub_limit：降低 chunk 行数。优先使用保守上限捷径（4a.3），而非逐个 buffer 调整。

---

## 5. 优化变换

基础形态：

```
for row_start in range(0, rows_per_worker, fixed_small_rows):
    rows = min(fixed_small_rows, rows_per_worker - row_start)
    current = load_current_block(row_start, rows)
    state = load_row_state(slot, row_start, rows)
    state_broadcast = broadcast_state(state, rows, row_width)

    if needs_previous:
        previous = load_previous_block(prev_slot, row_start, rows)
        current = combine(current, previous, state_broadcast)

    if is_final:
        current = normalize(current, state_broadcast)
        store_final(row_start, rows, current)
    else:
        store_accumulator(slot, row_start, rows, current)
```

优化形态：

```
chunk_rows = choose_chunk_rows(...)

# 行块从 row_start=0 开始单调递增，
# 非尾块 rows=chunk_rows，尾块 rows=剩余有效行数。
# 不重不漏。

for row_start, rows in iter_row_chunks(rows_per_worker, chunk_rows):
    current = load_current_block(row_start, rows)
    state = load_row_state(slot, row_start, rows)
    state_broadcast = broadcast_state(state, rows, row_width)

    if needs_previous:
        previous = load_previous_block(prev_slot, row_start, rows)
        current = combine(current, previous, state_broadcast)

    if is_final:
        current = normalize(current, state_broadcast)
        store_final(row_start, rows, current)
    else:
        store_accumulator(slot, row_start, rows, current)
```

关键点：

- 合并行块只改变每次处理的行数，不改变每行的公式。
- 状态读取、上一轮累加读取和最终写出都使用同一个局部 row offset 体系。
- 当前 slot 写出和上一 slot 读取不能别名。
- 尾块的 padding 只能用于满足 primitive 对齐，不允许写入最终有效输出。

---

## 6. 实施步骤

1. 定位向量后处理阶段中固定很小的 row chunk。
2. 列出该阶段每个 chunk 同时驻留的张量：当前输入、上一轮输入、输出、广播缓冲、scratch。
3. 计算旧 chunk 数、新 chunk 行数、新 chunk 数和向量 UB 占用（使用 4a 节的方法）。
4. 确认逐行状态缓存、GM/workspace 偏移和最终输出偏移都能按更大连续行块推进。
5. 将固定小 chunk 替换为容量驱动 chunk（含 UB 约束）。
6. 按新 chunk 行数调整广播缓冲和临时块容量；不要改变状态缓存语义。
7. 对首轮、非首轮、最终轮、非最终轮分别跑精度。
8. 用同一性能入口对比，若收益低于门槛则回滚。

不要在同一轮同时做：

- 改矩阵 tiling 或 L1 大块。
- 迁移状态到片上或从临时状态直写最终缓存。
- 缩减/重排 GM workspace。
- 改核间任务分配。
- 合并多个生命周期不同的向量阶段。

---

## 7. 正确性约束

必须满足：

- 合并后的 chunk 覆盖的行集合与原实现完全一致，不重不漏。
- 首轮不读取未初始化的上一轮累加。
- 非首轮读取的上一 slot 与当前写入 slot 不混淆。
- 最终轮只写真实有效行和真实有效列。
- 非最终轮写回的中间累加布局与后续读取布局一致。
- 广播状态只作用于对应行，不能跨行错位。
- dtype、舍入模式和每行内操作顺序保持一致。
- **总 UB 占用不超过硬件限制（4a 节）。**

高风险信号：

- `row_start` 使用全局行号，而状态缓存使用局部行号，或反之。
- chunk 行数不是广播对齐粒度的倍数，导致状态展开错位。
- 为大 chunk 临时降低队列深度后，MTE/V overlap 明显变差。
- 尾块 padding 被 cast 或写回到最终输出。
- 多个向量阶段共享同一 scratch，扩大 chunk 后生命周期重叠。
- chunk 值导致共享队列 slot 增大，总 UB 超过 192KB（4a 节）。

---

## 8. 验证流程

静态自检：

- 旧/new chunk 行数和 chunk 数。
- 每个 chunk 同时驻留的 buffer 字节数。
- 广播缓冲行对齐和尾块有效行。
- 当前 slot、上一 slot、最终输出的 row offset 映射。
- 是否新增 GM 访问：应为否。
- **total_ub ≤ ub_limit：应为是（使用 4a 节计算）。**

动态验证：

- 基础精度通过。
- 全量精度通过。
- 性能使用同一设备、同一 warmup/repeat、同一 benchmark case。
- 平均耗时提升超过 `1%` 才认为本策略有效。
- 如果性能变化在 `±1%` 内，视为无显著收益并回滚或标记不适用。

### 8a. 运行时错误诊断指南

> **本节补充运行时错误的关键诊断知识。** UB 溢出错误在运行时才暴露，且错误信息混合了 Vec 侧和 Cube 侧的描述，容易误判。

#### 8a.1 UB 溢出的典型错误模式

当 chunk 行数导致总 UB 超过硬件限制时，运行时出现以下 aicore exception：

**主错误**（判定性）：
```
VEC instruction error: the ub address out of bounds
```
看到此信息 → **立即判定为 UB 溢出**。

**次生错误**（误导性）：
```
CCU instruction address check error
fixp_error0 info: 0xa9, fixp_error1 info: 0x1a
```
这是 Vec 侧 UB 溢出导致的 Cube Fixpipe 地址错位，**不是 Cube 侧独立问题**。

> 不要被 CCU/Fixpipe 错误误导而排查 Cube kernel — 根因是 Vec 侧 UB 分配超限。

#### 8a.2 诊断步骤

1. 检查 aicore exception 信息是否包含 "ub address out of bounds"。
2. 若包含 → 使用 4a.4 节公式计算 total_ub，确认是否超过 ub_limit。
3. 若超过 → 降低 chunk 行数。优先使用保守上限捷径（4a.3），而非逐个 buffer 调整。
4. 若不包含 → 排查其他运行时问题（slot 映射错误、精度偏移、GM 地址越界等）。

#### 8a.3 UB 溢出 vs 其他运行时错误

| 错误类型 | 特征 | 诊断方法 |
|---|---|---|
| UB 溢出 | kernel 完全崩溃，aicore exception 包含 "ub address out of bounds" | 计算 total_ub vs ub_limit |
| 精度错误 | kernel 正常运行但数值偏差超阈值 | 检查 row offset、slot、尾块 |
| GM 地址越界 | aicore exception 包含 "GM address" 相关信息 | 检查 workspace offset 计算 |

---

## 9. 回滚规则

| 失败类型 | 信号 | 处理 |
|---|---|---|
| 精度失败 | 行错位、首轮/尾块异常 | 恢复固定小 chunk，检查 row offset 和尾块 |
| UB 容量失败 | 运行时 "ub address out of bounds" | **优先使用保守上限捷径（4a.3）降低 chunk**，而非逐个 buffer 调整 |
| 性能持平 | chunk 数下降但耗时无变化 | 判定后处理不是热点，回滚 |
| 性能回退 | 队列 overlap 下降或 scratch 冲突 | 降低 chunk 行数，恢复队列深度 |
| 尾块失败 | 非整行场景误差或越界 | 修正有效行/列处理，必要时尾块走旧路径 |

降阶顺序：

1. 从最大容量 chunk 降到保守上限 chunk（4a.3 捷径值）。
2. 进一步降低到较小但仍大于旧值的对齐 chunk。
3. 只在行数足够大的 shape 启用。
4. 仅对非最终轮或最终轮中的一个子路径启用。
5. 完全恢复固定小 chunk。

---

## 10. 给实现 LLM 的检查清单

实现前：

- 确认本策略不是 L1 大块、reduce 轴大块化、状态 GM 往返消除或状态直写缓存。
- 找到向量后处理阶段中固定很小的 row chunk。
- 计算旧/new chunk 数、容量占用和广播对齐。
- **计算 total_ub ≤ ub_limit（使用 4a 节），确认 chunk 值不会导致 UB 溢出。**
- **优先使用保守上限捷径（4a.3）确定 chunk 值，避免复杂的逐 buffer 计算。**
- 证明合并多行不会改变每行公式或状态 slot 语义。

实现中：

- 只改后处理 row chunk 选择和必要的向量临时容量。
- 保持矩阵阶段、任务划分、状态缓存语义和 GM workspace 语义不变。
- 对首轮/非首轮、最终/非最终路径都使用同一 row offset 体系。
- 尾块只处理有效行列。

实现后：

- 基础和全量精度通过。
- **若出现 "ub address out of bounds" 错误 → 按 8a 节诊断，降低 chunk 值。**
- 使用同链路性能数据判断保留或回滚。
- 性能变化在 `±1%` 内视为无显著收益。

---

## 11. 文档自检

- 未包含具体算子名。
- 未包含具体源文件名。
- 未包含具体函数名。
- 未包含 AscendC 实现代码片段。
- 未复制或泄漏高性能实现代码。
- 只使用 Python 风格伪代码、抽象 helper、适用条件、收益模型、验证流程和回滚规则。
- UB 约束公式和硬件参考值使用通用表达，不含特定算子参数。

## 检索卡（短卡）

动作：将向量后处理的固定小逐行块改为容量驱动的行块合并
适用：后处理逐行独立、合并不改变行间顺序语义，且当前阶段可一次处理连续多行。
限制：合并前后行集合须一致且不重不漏；首轮不得读取未初始化的上一轮累加
范围：矩阵输出后的向量后处理阶段
检索词：row chunk、向量队列容量、元素宽度、广播对齐、UB 安全预算
机会：小行块反复读取当前输出块及可选的上一轮累加块
