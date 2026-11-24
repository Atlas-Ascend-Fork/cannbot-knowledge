---
type: Optimization
title: per-row 状态片上通路优化（子模式 A：消除 GM workspace 往返；子模式 B：消除片上二次拷贝）
description: 将 per-row 状态由写入 GM 后回读改为直接保留在片上供后续阶段消费。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/03-onchip-state-cache.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：per-row 状态片上通路优化（子模式 A：消除 GM workspace 往返；子模式 B：消除片上二次拷贝）

> **单一优化点（双子模式）：** 本文处理同一条数据通路（向量阶段产生 per-row 小中间量 → 中转 → 消费阶段读取）上的**两段不同浪费**，按顺序实施：
>
> - **子模式 A（消除 GM 往返，本文件主体）：** 当向量阶段生成的 per-row 小型中间量只在同一核、同一 kernel 内被后续阶段消费时，不再将其写入 GM workspace 后再读回，而是直接保留在消费阶段可安全读取的片上 `LocalTensor/TBuf` 切片中。消除热点循环内的小型 GM 读写及其 MTE 搬运/等待/地址计算。
> - **子模式 B（消除片上二次拷贝，原 04-state-direct-cache-write 已并入）：** 当中间量已经在片上，但 primitive 先输出到临时 `LocalTensor`、再从临时拷贝到目标 `LocalTensor` 切片时，把 primitive 的输出直接绑定到后续阶段真实读取的目标 `LocalTensor` 切片，删除 `tmp_local → target_local` 二次拷贝与只用于中转的临时缓冲。**典型在子模式 A 之后实施**——先消除 GM workspace 往返，热点路径若仍存在 tmp→target 二次拷贝，再由 B 收尾。

本文中的 **per-row 小型中间量** 指每行一个或少量元素、生命周期很短的中间状态，例如 row max、row sum、scale、归一化统计量、累计更新系数、在线更新系数等。

它不包括：

- 跨核 reduce 或跨 task 合并状态。
- 后续 kernel 需要读取的 workspace。
- host、debug dump 或校验流程需要观测的数据。
- tiling 参数、流水控制元数据、全局调度状态。
- 大块 tensor、矩阵 tile、L1 驻留块。

两个子模式都不改变数学公式、在线更新顺序、矩阵 tile、L0/L1 微块、blockDim、tiling、跨核任务划分或输入输出布局。首轮实现只迁移一个生命周期最明确、最热点的 per-row 小中间量；workspace 缩容不是本轮必要改动。

---

## 1. AscendC 语义依据

AscendC 中，`GlobalTensor` 表示 Global Memory 上的数据，`LocalTensor` 表示 AI Core Local Memory 上的数据。向量计算通常以 `LocalTensor` 为操作数；`TBuf` 可管理计算过程中的临时片上缓存；`TQue` 用于搬入、计算、搬出阶段之间的队列化同步和生命周期管理。

因此，只有当中间量不需要 Global Memory 可见性，并且生产者与消费者都在同一核、同一 kernel、同一执行上下文内时，才可以把 GM workspace 往返替换为片上 `LocalTensor/TBuf` 复用。

---

## 2. 性能问题模式

**子模式 A** 寻找以下代码模式：

1. 阶段 A 在向量计算中生成每行一个或少量元素的小中间量。
2. 阶段 A 将该中间量写入 `workspace`、`GlobalTensor`、`tmpGm`、`stateGm` 等 GM 临时区。
3. 阶段 B 在同一 kernel、同一核、同一流水上下文中又从 GM 读回。
4. 阶段 B 将该中间量按行广播，用于缩放、归一化、累计更新或后续向量计算。

典型收益来自消除：

- 热点循环内的小型 GM 写。
- 热点循环内的小型 GM 读。
- 对应的 MTE 搬运、等待、地址计算和 workspace 带宽消耗。

若该 GM 往返只发生在一次性初始化路径，或 profiling 显示该搬运已被完全隐藏，则不应实施本策略。

**子模式 B** 寻找以下代码模式（典型出现在子模式 A 之后的代码里）：

1. 向量 primitive 处理一个 row chunk。
2. primitive 输出 per-row 小型中间量到临时 `LocalTensor`（名称类似 `tmpState`、`stateTmp`、`reduceTmp`、`softmaxTmp`、`rowTmp`、`tmpMax`、`tmpSum`）。
3. 代码再执行 `tmp_local → target_local` 的片上拷贝、vector copy、`DataCopy`、`SetValue/GetValue` 循环或等价搬运。
4. 后续阶段从 `target_local` 读取该中间量。
5. 临时 `tmp_local` 除了承接 primitive 输出并拷贝到目标缓存外，没有独立语义。

典型收益来自消除：热点循环内的片上二次拷贝及其向量流水依赖等待、只用于中转的临时缓冲占用（UB/Local Memory）。

---

## 3. 适用条件

**子模式 A** 必须同时满足：

| 条件 | 要求 |
|---|---|
| 生命周期短 | 只覆盖当前任务、当前流水阶段或相邻阶段；若原实现跨 slot 保留，则必须保留 slot 语义 |
| 消费者固定 | 消费发生在同一核、同一 kernel、同一向量执行上下文 |
| 不需要 GM 语义 | 其他核、后续 kernel、host、debug dump 不依赖该 workspace 数据 |
| 目标缓存明确 | 能明确消费代码将从哪个片上 tensor 切片读取该值；分配、释放、position、row/slot offset、对齐和生命周期均可静态说明 |
| 规模小 | `scope_count * aligned_bytes_per_scope` 能放入可用片上缓存预算 |
| 映射一致 | 生产和消费使用同一 `local_row_offset`；若存在流水 slot，则 slot 映射也必须一致 |
| 标量消费安全 | 若后续消费者通过 `GetValue` 或标量读获取每行状态，必须保留短生命周期 staging tensor，不得直接把长期 ring cache slice 传给该消费者 |
| 输出等价 | 不改变初始值、在线更新顺序、尾块规则和浮点语义 |

**子模式 B** 必须同时满足（在 A 的基础上替换"不需要 GM 语义"为下列条件）：

| 条件 | 要求 |
|---|---|
| 临时缓冲无独立用途 | 原临时 `LocalTensor` 除拷贝进目标切片外，不被其他逻辑读取、复用、dump 或参与同步语义 |
| primitive 支持直写 | primitive/helper 支持调用者传入输出 `LocalTensor`，且允许目标切片 offset、长度、dtype、连续度和别名关系 |
| 输出布局兼容 | 目标切片的 stride、padding、连续度和起始地址满足 primitive 写入契约和后续向量 API 对齐要求 |
| 生命周期安全 | 当前输出不会覆盖上一轮输入、默认初始值、仍在消费的数据或 TQue 尚未释放的数据 |

优先适用场景：

- online softmax、归一化、reduce + broadcast、分块累计更新。
- 每行标量或短向量后续被广播到整行或整块。
- 热点循环中反复出现小型 workspace 写后读（A）/ 片上 tmp→target 拷贝（B）。
- 当前实现已有部分 per-row 状态片上保留，但仍有同生命周期状态绕行 GM（A）；已消除 GM 往返后热点路径仍有二次拷贝、UB 占用较紧（B）。

不适合场景：

- 中间量需要跨核 reduce、跨 task 合并或后续 kernel 读取。
- 中间量被 host、debug dump、校验逻辑或外部工具依赖。
- 生产和消费的 row split 不一致，需要复杂重排。
- 为保存小状态会挤压主要输入、输出队列或破坏 double buffer。
- 瓶颈明确在计算或大 tensor 搬运，小型 GM 往返/片上拷贝占比低。
- 需要强行改变已有 `LocalTensor` position、`TQue` 生命周期或 slot 语义。
- 子模式 B 额外不适合：primitive 不支持指定输出 `LocalTensor` 或不支持从目标 offset 切片写入；primitive 要求输出从 offset 0 开始而目标切片无法提供等价对齐；临时缓冲承担必要的 pack/unpack/transpose/align/reorder/dtype convert；临时输出有多个消费者且需要不同布局；临时缓冲承载必要同步边界；为满足直写对齐需显著缩小主 vector chunk（新增循环开销超过拷贝节省）。

---

## 4. 目标片上缓存选择规则（A/B 共用）

目标片上缓存是消费阶段可安全读取的 `LocalTensor/TBuf` 切片。它不一定是 slot 化缓存，也不一定必须是 `TBuf<TPosition::VECCALC>`。

选择顺序：

1. **优先复用消费阶段已经读取或可安全改为读取的片上 tensor 切片**（子模式 B 即"原二次拷贝后的目标切片"）。
2. 若原数据流按流水 slot 保留该状态，则保留 slot 维度，例如：

   ```python
   target_cache[slot_id][local_row_offset][item]
   ```

3. 若生产后立即消费、没有跨 slot 生命周期重叠，则使用非 slot 化布局：

   ```python
   target_cache[local_row_offset][item]
   ```

4. 若需要新建短生命周期缓存，通常优先使用：

   ```cpp
   TBuf<TPosition::VECCALC> rowStateBuf;
   ```

5. 若目标属于已有 `VECOUT`、`TQue` 或其他合法 position，应保持原数据流语义，不为套用策略强制改成 `VECCALC`。

禁止行为：

- 不要凭空选择一个“看起来空闲”的 `LocalTensor` 保存状态。
- 不要把输入/输出队列 tensor 当成任意长期 scratch。
- 不要为本策略强行引入 slot。
- 不要为本策略强行删除原有 slot。
- 不要用普通 C++ 数组替代 AscendC `LocalTensor/TBuf`。
- 不要让当前输出覆盖上一轮仍需读取的状态；不要把默认初始值缓冲作为 primitive 输出目标（B）。

---

## 5. TQue 与生命周期约束（A/B 共用）

若目标 tensor 来自 `TQue`，必须遵守原有 `AllocTensor / EnQue / DeQue / FreeTensor` 生命周期。

要求：

- 不得在 `FreeTensor` 后继续保存或读取状态。
- 不得跨 `EnQue/DeQue` 边界绕开原同步语义读写。
- 不得把 `TQue` 管理的输入、输出 tensor 当成长期缓存。
- 只有当 per-row 状态的生产、消费与该 queue tensor 生命周期完全一致时，才允许复用。
- 若状态生命周期长于 queue tensor 生命周期，必须使用独立 `TBuf` 或回退 GM workspace。
- 若原拷贝同时承担"写完后再消费"的顺序约束（B），删除拷贝时必须保留等价同步或顺序保证。

若使用 `TBuf`（子模式 B 常见）：`TBuf.Get<T>()` 得到的 `LocalTensor` 无需 `FreeTensor`，但其生命周期仍不能越过覆盖或复用边界；删除临时 `TBuf` 前，必须确认没有其他路径读取它。

---

## 6. 对齐与容量计算（A/B 共用）

**子模式 A** 容量估算：

```python
row_item_bytes = items_per_row * dtype_bytes
scope_stride_bytes = align_up(aligned_rows * row_item_bytes, 32)

old_gm_bytes_per_outer = scope_stride_bytes * (gm_write_count + gm_read_count)
saved_gm_bytes = outer_iterations * old_gm_bytes_per_outer

scope_count = slot_count if need_slot_cache else 1
onchip_bytes = scope_count * scope_stride_bytes
```

**子模式 B** 净占用模型：

```python
valid_payload_bytes = valid_rows * items_per_row * dtype_bytes
copy_bytes_per_chunk = align_up(aligned_rows * items_per_row * dtype_bytes, 32)

removed_onchip_copy_bytes = (
    outer_iterations
    * row_chunks_per_outer
    * target_item_group_count
    * copy_bytes_per_chunk
)

removed_temp_bytes = target_item_group_count * temp_buffer_capacity_bytes
added_target_padding_bytes = new_target_cache_bytes - old_target_cache_bytes

net_local_saving = removed_temp_bytes - max(0, added_target_padding_bytes)
```

对齐规则（A/B 共用）：

- 总 buffer 起始地址需要满足后续 API 的对齐要求。
- 每个 slot 起始地址（及子模式 B 的每个目标切片起始地址）需要按实际访问粒度对齐。
- 每行或每个 scope 的 stride 不能只按有效元素数计算，必须按后续向量 API 的访问粒度对齐。
- 尾行只写入和读取有效行；尾列广播只作用于有效列。
- 若容量不足或挤压主要输入/输出队列，回退 GM workspace（A）/ 原二次拷贝路径（B）。

进入实现的门槛：

- 消除的 GM 读写/片上拷贝位于热点循环（而非一次性初始化路径）。
- `onchip_bytes` 明显小于可用片上缓存预算（A）；`net_local_saving > 0` 或虽总占用不降但能删除明确的热点片上拷贝和依赖等待（B）。
- row 映射、slot 映射、尾块规则可以保持不变。
- 预期收益超过测量噪声，建议理论上界至少超过 1%。

GM 字节下降只是候选信号，不等于端到端收益。若性能持平或回退，应以实测结果为准。

---

## 7. 改写模板

### 7.1 新建短生命周期 TBuf

仅当无法安全复用已有目标 tensor 时使用：

```cpp
TBuf<TPosition::VECCALC> rowStateBuf;
pipe.InitBuffer(rowStateBuf, rowStateCacheBytes);
auto rowStateLocal = rowStateBuf.Get<T>();
```

### 7.2 写入片上缓存

由：

```cpp
auto state = compute_per_row_state(...);
write_global(workspaceGm, optionalSlot, rowOffset, state);
```

改为：

```cpp
auto state = compute_per_row_state(...);
uint32_t offset = localRowOffset * itemsPerRow;
if (needSlotCache) {
    offset = slotId * slotStride + localRowOffset * itemsPerRow;
}
write_local(rowStateLocal, offset, state);
```

### 7.3 从片上缓存读取

由：

```cpp
auto state = read_global(workspaceGm, optionalSlot, rowOffset);
broadcast_and_compute(state, ...);
```

改为：

```cpp
uint32_t offset = localRowOffset * itemsPerRow;
if (needSlotCache) {
    uint32_t consumeSlot = slotId;  // 或 previous_slot(slotId)，必须与原流水语义一致
    offset = consumeSlot * slotStride + localRowOffset * itemsPerRow;
}
auto state = read_local(rowStateLocal, offset);
broadcast_and_compute(state, ...);
```

注意：

- `slotId` 必须来自现有流水索引，例如 `progress % BUFFER_NUM`。
- `localRowOffset` 使用当前任务或当前子块的局部行号，不要混用全局 row id。
- 若没有跨 slot 生命周期，不要引入 slot 维度。
- 若需要读取上一 slot，环形索引必须与原实现一致。

### 7.4 子模式 B：primitive 直写目标切片

低效形态：

```python
for chunk in row_chunks:
    data = load_vector_chunk(chunk)

    tmp_local = allocate_temp_per_row_tmp(chunk.rows, item_count)
    output, tmp_local = online_vector_update(
        data=data,
        prev_tmp=read_prev_tmp(chunk),
        tmp_out=tmp_local,
    )

    copy_onchip(
        dst=target_local_slice(chunk),
        src=tmp_local,
        rows=chunk.valid_rows,
    )

    forward_output(output)
```

优化形态（primitive 输出直接绑定目标切片，删除二次拷贝与临时缓冲）：

```python
for chunk in row_chunks:
    data = load_vector_chunk(chunk)

    tmp_out = target_local_slice(
        local_row_offset=chunk.local_row_offset,
        rows=chunk.valid_rows,
    )

    output, _ = online_vector_update(
        data=data,
        prev_tmp=read_prev_tmp(chunk),
        tmp_out=tmp_out,
    )

    forward_output(output)
```

若原实现存在流水 slot：

```python
tmp_out = target_local_slice(
    slot=slot_id,
    local_row_offset=chunk.local_row_offset,
    rows=chunk.valid_rows,
)
```

抽象 helper 契约：

```python
def target_local_slice(local_row_offset, rows, align_rows, slot=None):
    """
    返回可被 primitive 直接写入的连续片上切片。
    local_row_offset 必须是当前任务/子块内局部行偏移。
    slot 仅在原实现存在跨 slot 生命周期时使用。
    rows 表示有效行；padding 区可以被写入，但不能参与语义。
    返回切片的起始地址、stride、长度、dtype、position 必须满足 primitive 和后续向量 API 契约。
    """
```

关键约束：

- `prev_tmp` 与 `tmp_out` 必须是不同生命周期的切片。
- 当前输出不能覆盖上一轮输入、默认值或仍在消费的目标 cache。
- 默认初始值仍来自只读默认缓冲。
- 若 primitive 要求输出地址按若干行或字节对齐，chunk 起点、目标 stride 和 padding 必须同时满足。
- padding 区可以写入，但后续阶段不得按有效行读取。

---

## 8. SetValue / GetValue 使用限制

不要把向量 API 产生的一批 per-row 状态改成大量 `SetValue/GetValue` 标量循环。

优先级：

1. 优先让 reduce、compute、copy 或 vector API 直接写入目标 `LocalTensor` 切片。
2. 若原实现已经产生 `LocalTensor` 结果，优先改后续消费者读取该结果。
3. 只有极少量标量、初始化分支或不可向量化控制值，才允许使用标量访问。
4. 若为了上片导致大量标量循环，通常应回退 GM workspace 或重新选择目标中间量。

### 8.1 标量消费者的 staging 红线

当后续消费者内部通过 `GetValue` 或等价的标量 S-pipeline 读逐行状态时，片上缓存只能替代 GM backing store，不能同时删除短生命周期 staging 边界。典型消费者包括按行缩放或归一化的封装（形如"逐行乘以 per-row scale"、"逐行除以 per-row sum"一类接受 per-row 状态指针/切片的 helper）。

禁止把长期 ring cache slice 直接传给这些消费者：

```cpp
auto scaleA = stateCacheUb_[slot * stateStride + globalRow];   // 长期 ring cache 切片
auto scaleB = stateCache2Ub_[slot * stateStride + globalRow];
RowScaleImpl(outUb, outUb, scaleA, dealRows, dim);             // 标量消费者直接读长期 cache —— 禁止
RowScaleImpl(out2Ub, out2Ub, scaleB, dealRows, dim);
```

正确做法是在消费侧保留一个短生命周期 staged tensor，把当前 row chunk 从长期 cache 拷入 staged tensor，再在必要的 pipeline barrier 之后交给标量消费者：

```cpp
Adds(readStagedA, stateCacheUb_[slot * stateStride + globalRow], 0.0f, dealRows);
Adds(readStagedB, stateCache2Ub_[slot * stateStride + globalRow], 0.0f, dealRows);
PipeBarrier<PIPE_V>();
RowScaleImpl(outUb, outUb, readStagedA, dealRows, dim);
RowScaleImpl(out2Ub, out2Ub, readStagedB, dealRows, dim);
```

这个 staged tensor 可以是新增 `TBuf<TPosition::VECCALC>`，也可以是原实现已经用于 GM 读回后的临时 `LocalTensor`。本策略的优化目标是消除 GM 往返，而不是消除所有片上 staging。若删除 staging 会让标量消费者直接读取长期 ring cache，必须视为策略实现错误。

---

## 9. LLM 修改前必须回答的问题

实施前必须在优化记录中回答：

| 问题 | 必填内容 |
|---|---|
| 迁移哪个变量 | 名称、dtype、每行元素数 |
| GM 写在哪里 | 函数、loop、offset、写入次数 |
| GM 读在哪里 | 函数、loop、offset、读取次数 |
| 是否只有同核同 kernel 消费 | 是否有其他核、后续 kernel、host、debug 读者 |
| 消费代码改读哪个片上缓存 | tensor 名称、position、是否已有 |
| row 映射是否一致 | 生产和消费是否使用同一 `local_row_offset` |
| 是否需要 slot | 不需要 / 当前 slot / 上一 slot；slot 来源是什么 |
| 新增片上占用 | 每 scope 字节数、scope 数、总字节数、对齐后 stride |
| 初始值如何处理 | 独立只读缓冲 / 显式初始化 / `is_first` 分支 |
| TQue 生命周期是否安全 | 是否跨 `FreeTensor`、`EnQue/DeQue` 边界 |
| 标量消费者是否保留 staging | 若通过 `GetValue` 或等价标量路径消费 per-row 状态，说明 staged tensor 和 barrier |
| 尾块规则 | 有效行、有效列、广播 mask 或边界判断 |
| 子模式 B（如实施） | primitive 在哪里输出；原临时缓冲名称/position/容量/分配位置；二次拷贝位置（copy/helper/DataCopy/vector copy/SetValue 循环）；临时缓冲是否有其他消费者（有则禁止）；primitive 是否支持直写（offset、连续度、长度、dtype、别名）；别名风险（prev/default/current output/TQue tensor 是否重叠）；删除拷贝字节、删除临时 buffer 字节、目标 padding 增量、净片上占用变化 |

若任一问题无法回答，不实施本策略。

---

## 10. 正确性红线

必须满足：

- `is_first` 或初始化分支不能读取未初始化片上缓存。
- 生产写入完成后，消费阶段才能读取。
- 若使用 slot 化缓存，slot 复用前旧状态必须已经不再需要。
- 若不使用 slot 化缓存，必须证明生产、消费和覆盖之间没有生命周期重叠。
- 生产和消费必须映射到同一 `local_row_offset`。
- 初始默认值不能被在线更新覆盖。
- 尾行、尾列只处理有效数据。
- 新增或复用的片上缓存不得与正在使用的输入、输出、临时 tensor 发生未同步覆盖。
- 目标 tensor 的 position 必须与后续 API 和原数据流语义兼容。
- 不得为了保存小状态减少主要输入/输出队列 buffer 数。

高风险信号：

- 生产按全局行号写，消费按局部行号读。
- stride 小于对齐后的实际访问范围。
- 读取来自另一个核、另一个 task 或后续 kernel。
- 强行引入 slot 导致片上缓存占用上升。
- 强行去掉 slot 导致流水覆盖。
- 一次迁移多个不同生命周期中间量。
- 为迁移小状态引入大量 `SetValue/GetValue` 标量循环。
- 直写目标与输入切片、默认缓冲或上一轮切片可能重叠（B）。
- 为满足对齐把主 chunk 切得过碎（B）。
- 删除临时缓冲后，某个后续逻辑仍读取临时中间量（B）。
- 多个中间量共用连续缓存，但宽度或对齐不同，导致第二个中间量起点错位（B）。
- 删除拷贝时连带删除了仍承担生产-消费顺序保证的必要同步（B——只有能证明同步只保护被删除拷贝时才可删）。

---

## 11. 实施步骤

### Step 1：识别目标中间量

寻找热点循环内的 `workspace/GlobalTensor/tmpGm/stateGm` 写后读模式。优先选择最小、最热点、生命周期最明确的一个 per-row 状态。

### Step 2：建立映射表

记录 GM 写入位置、GM 读回位置、row offset、slot 规则、目标片上缓存、position、对齐、容量、初始化和外部可见性。

### Step 3：复用或新建目标缓存

优先复用消费阶段可安全读取的片上 tensor。无法复用时，新建短生命周期 `TBuf<TPosition::VECCALC>`。不要修改 tiling、blockDim、矩阵 tile 或跨核任务划分。

### Step 4：替换 GM 写入和读回

只替换目标中间量的 GM 往返：

- GM 写入改为写 `LocalTensor/TBuf` 切片。
- GM 读回改为读同一片上切片。
- 保持原始计算顺序、初始值、尾块规则和 slot 语义。

### Step 5：保留 workspace 规划

首轮可以保留原 workspace 总大小和 offset 规划，只停止目标中间量的 GM 读写。确认正确性和收益后，再考虑清理未使用 workspace 段。

---

## 12. 验证流程

### A. 基线验证

- clean build 通过。
- 基础精度通过。
- 记录基线性能：均值、最小值、波动范围。

### B. 静态映射验证

必须确认：

- 目标中间量不需要跨核、跨 kernel、host 可见。
- 生产和消费 row offset 一致。
- slot 规则与原流水一致。
- 片上容量和对齐满足要求。
- `TQue` 生命周期不被破坏。
- 初始值和尾块规则明确。

### C. 单变量替换

只迁移一个 per-row 状态。精度通过后，才能考虑同生命周期的其他状态。不同生命周期的状态不得在同一轮迁移。

### D. 性能确认

- 使用同一评测入口、同一设备、同一 warmup/repeat。
- 对比优化前后均值、最小值和波动。
- 变化在 ±1% 内视为无显著收益。
- 若性能持平或回退，以实测为准回滚或保守保留。

---

## 13. 回滚规则

| 失败类型 | 典型信号 | 处理 |
|---|---|---|
| 精度失败 | 第一块、跨 slot、跨轮结果异常 | 检查初始化、slot 索引、row offset、覆盖关系；B 检查默认初始值、上一轮读取、当前写入是否混淆 |
| 尾块失败 | 非整行/非整列 shape 误差大 | 检查有效行列、mask、对齐 stride |
| 容量失败 | 编译或运行提示片上缓存不足 | 回退 GM workspace（A）；恢复临时缓冲、降低直写范围（B） |
| 性能持平 | GM 流量下降但耗时无变化 | 判定非热点，回滚或保守保留 |
| 性能回退 | 队列 buffer 减少、临时区挤压、标量循环增多 | 回滚片上缓存路径（A）；回退对齐/stride 改动，恢复原路径（B） |
| GM 语义破坏 | 其他核、kernel、host 读不到数据 | 该中间量必须留在 GM |
| 生命周期破坏 | 去掉或引入 slot 后结果异常 | 恢复原 slot / 非 slot 语义 |
| 同步失败（B） | 删除拷贝后读到旧值或未写完数据 | 恢复必要同步或原片上拷贝 |

降阶顺序：

1. 只迁移单个中间量，其他中间量保持 GM（A）/ 保留临时缓冲（B）。
2. 只覆盖热点 shape 或减少缓存覆盖行数；B 只在对齐天然满足的 shape 启用，或保留临时缓冲但删除非必要额外 copy。
3. 完全回退目标中间量到 GM workspace（A）/ 完全恢复 `primitive → tmp_local → target_local` 路径（B）。

---

## 14. Checklist

实现前：

- [ ] 确认本轮不是 L1 大块驻留、tiling 调整或 blockDim 调整。
- [ ] 找到热点循环内“写 GM 后又读回”的 per-row 小型中间量。
- [ ] 证明该中间量不需要跨核、跨 kernel、跨 task、host 或 debug 可见。
- [ ] 找到消费阶段可安全读取的目标 `LocalTensor/TBuf`。
- [ ] 明确该目标 tensor 的 position、分配、释放和生命周期。
- [ ] 判断是否真的需要 slot；需要则保留，不需要则不强加。
- [ ] 写清 `local_row_offset`、slot 来源、stride、尾块规则。
- [ ] 计算 `saved_gm_bytes` 和 `onchip_bytes`，并按实际访问粒度对齐。
- [ ] 确认不会挤压主要输入/输出队列。
- [ ] 确认不会引入大量 `SetValue/GetValue` 标量循环。

实现中：

- [ ] 只替换目标中间量的 GM 写和 GM 读。
- [ ] 不改变数学公式、在线更新顺序、矩阵 tile、blockDim、tiling 或跨核划分。
- [ ] 初始默认值与可变缓存分离。
- [ ] 保持生产和消费顺序。
- [ ] 保持原 slot / 非 slot 语义。
- [ ] 尾块只处理真实有效行列。
- [ ] 遵守 `TQue` 的 `AllocTensor / EnQue / DeQue / FreeTensor` 生命周期。
- [ ] 首轮保留原 workspace 规划，不混入 workspace 缩容。

实现后：

- [ ] clean build 通过。
- [ ] 基础和全量精度通过。
- [ ] 对比同链路性能，记录均值、最小值、波动。
- [ ] 若性能持平或回退，按回滚规则处理。
- [ ] 记录是否仍保留未使用 workspace 段；清理不属于本轮必要优化。

---

## 15. 策略标签

```yaml
strategy_category: AscendC / Vector / Workspace Traffic & On-chip Copy Elimination
optimization_type:
  mode_a: GM workspace read/write elimination
  mode_b: LocalTensor intermediate copy elimination
mode_order: B is typically applied after A has eliminated the GM round-trip
target_state: per-row reduce/stat/scale/update state
first_round_scope: migrate exactly one short-lived per-row state
forbidden_mixed_changes:
  - tiling adjustment
  - blockDim adjustment
  - matrix tile change
  - L1 large-block residency
  - cross-core scheduling change
  - workspace size shrink as required change
  - multiple states with different lifetimes
  - main vector chunk shrink (B)
  - TQue buffer count reduction (B)
rollback_threshold: performance_gain < 1%
```

## 检索卡（短卡）

动作：将 per-row 状态由写入 GM 后回读改为直接保留在片上供后续阶段消费。
适用：状态生命周期仅覆盖当前任务或相邻阶段；跨 slot 时须保留 slot 语义。
限制：来自 TQue 的 tensor 必须遵守原 Alloc、入队、出队和释放生命周期。
范围：同一核、同一 kernel 内跨相邻阶段的 per-row 状态。
检索词：per-row 状态、片上缓存、GM workspace、写后读、TQue。
机会：热点循环存在 workspace、GlobalTensor、tmpGm 或 stateGm 写后读。
