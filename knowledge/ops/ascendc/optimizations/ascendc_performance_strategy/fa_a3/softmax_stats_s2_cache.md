---
type: Optimization
title: 循环不变统计量的跨外层迭代片上缓存，消除重复 GM 搬运
description: 将循环不变统计量缓存在持久UB中，跨外层迭代复用，消除重复GM搬运。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/02-softmax-stats-s2-cache.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：循环不变统计量的跨外层迭代片上缓存，消除重复 GM 搬运

> **单一优化点：** 当某组逐行（或逐组）统计量在 kernel 的外层循环维度上保持不变（其 GM 地址/偏移仅依赖一组不含该外层维度的索引），却仍在每次外层迭代中被重复从 GM 搬入片上 UB 时，改为仅在首次外层迭代搬入并缓存到持久 UB，后续迭代直接复用 UB 数据，从而消除重复 MTE2 搬运。外层迭代数越大，收益越显著。

---

## 1. 原理

### 问题：循环不变量被重复搬运

考察如下典型 kernel 结构：

```text
for task in tasks:                       // 某个外层任务/索引组合
    for outerIter in [0, outerCount):     // 外层分块迭代，outerCount > 1
        stageA(...)                       // 产生/使用 workspace
        consumeStats(outerIter)           // 在此处把统计量从 GM 搬入 UB
        stageB(...)                       // 下游向量计算消费统计量
```

`consumeStats` 每次被调用时都从 GM 搬入一组统计量。设统计量的 GM 偏移公式为 `offset = f(indexSet)`，其中 `indexSet` 是一组索引的函数。**关键判据**：若 `indexSet` 不包含 `outerIter`，则该统计量在外层迭代上是不变量，但当前实现却搬了 `outerCount` 次，其中 `outerCount-1` 次是冗余的。

每次搬运往往是「行粒度的循环 + 极小 DataCopy」，真正代价是 **MTE2 启动开销**（启动次数多、每次搬运字节数小、效率低），而非带宽。

### 解法：分配持久 UB，按统计量的不变维度分区缓存

增加一个专用持久 UB buffer（`TBuf<TPosition::VECCALC>`），容量须覆盖该统计量的**完整不变范围**（即 `indexSet` 所张成的最大行/组数 × 每行/组统计量宽度 × sizeof(元素类型)）。布局：按 `indexSet` 中在搬运点处被迭代的那一个子索引进行分区。

逻辑改为：

```text
partitionOffset = subIndex * statWidth          // subIndex 是不变索引集中、在搬运点迭代的子索引
totalMaxRegion  = maxExtentOf(indexSet) * statWidth
cacheMaxOff = partitionOffset
cacheSumOff = totalMaxRegion + partitionOffset      // 第二类统计量（如 sum）放在 max 区之后

if (outerIter == 0) {
    // 仅首次外层迭代从 GM 搬入并缓存
    for each row/group in this sub-partition:
        DataCopy(ubCache[cacheMaxOff + row*statWidth], statsMaxGm[baseOffset + row*stride], statWidth)
        DataCopy(ubCache[cacheSumOff + row*statWidth], statsSumGm[baseOffset + row*stride], statWidth)
    SetWaitFlag<MTE2_V>()   // 等待 GM->UB 拷贝完成，V pipe 才能读
}
// outerIter > 0：UB 数据已就绪，直接进入下游向量计算
```

下游消费方统一改为通过 `ubCache[cacheMaxOff]` / `ubCache[cacheSumOff]` 引用缓存数据。

---

## 2. 适用场景识别

应实施的情况（同时满足）：

1. 存在一个外层循环，运行时实际迭代数 > 1（不是恒为 1）。
2. 被重复搬运的统计量的 GM 偏移/地址公式**可证明不含该外层循环索引**（逐行核查偏移计算式，而非凭直觉）。
3. 该搬运是 GM->UB（MTE2）的真实重复传输，且以「多次小拷贝」形式呈现（MTE2 启动开销主导）。
4. UB 容量可容纳该统计量的完整不变范围，且不挤占其他同时存活的 tensor。
5. 首次迭代条件在搬运点可观测（外层迭代计数器可传入或已可用）。

不应实施的情况（任一满足即跳过）：

- 外层迭代数恒为 1（缓存无收益，徒增复杂度）。
- 统计量的偏移公式实际依赖外层索引（数据并非不变），缓存会返回陈旧值。
- 统计量在外层循环内会被原地修改（写后读、跨迭代依赖）。
- UB 容量不足以容纳完整不变范围（部分缓存会被后续子分区覆盖，比不缓存更糟）。
- 该数据已通过更廉价机制存在于某个存活片上 buffer（无需再缓存）。

Profiling 指征：MTE2 时间绝对值偏高、且 MTE2 启动次数多但每次搬运量极小（搬运效率低）。代码指征：出现「行粒度循环 + 小 DataCopy」且搬运目标偏移公式不含外层循环索引。

---

## 3. 正确性红线

**缓存区必须按统计量的不变维度分区，覆盖其完整不变范围（最易踩的坑）：**

若搬运点内部还按某个子索引（`subIndex`）分批循环，每个 `subIndex` 批对应不同行/组的统计量。若持久 UB 仅分配一个批次的容量，则后一个 `subIndex` 批写入时会覆盖前一个批次的缓存，导致外层迭代 >0 时读到错误批次的数据。

**必须按该子索引偏移分区**：`partitionOffset = subIndex * statWidth`，且缓存区容量必须为「`indexSet` 完整范围 × 统计量宽度 × sizeof(元素)」（覆盖该不变索引集的全部行/组，而非仅一个批次）。验证：分区数 × 每批缓存大小 == 分配容量，各分区无重叠、无越界。

**首次迭代条件必须真实生效：**

若外层迭代计数器在当前函数签名中被忽略（例如被 cast-to void 丢弃），必须先将其接入函数体，否则 `outerIter == 0` 的条件判断无法编译或行为未定义。

**MTE2→V 同步只在首次需要：**

首次迭代搬运后必须置 MTE2→V 等待，确保 V pipe 下游读到 MTE2 写入的数据。后续迭代跳过搬运，无需为该拷贝补充同步（UB 数据已在 V pipe 视野内，MTE2 未再写 UB）。注意：不得删除为其他无关 pipe 交互而存在的同步。

**被取代的 buffer 若曾被双重复用，须迁移其借用者：**

若新增的持久缓存取代了原先「同时被借用尾部空间作为 scratch 临时量」的 buffer，这些临时量必须迁移到其他已完成使命的片上区域。优先用 ReinterpretCast 复用一个已结束先前职责的 UB 区域，并确认复用保持在同一 pipe 内以避免引入新的跨 pipe 同步。

**UB 容量核算（禁止硬编码芯片 UB）：**

新增持久缓存后，须用目标芯片的真实 UB 容量（由 ascend-hardware 获取，不得硬编码具体芯片的 KB 数）重新核算总 UB 占用是否仍在上限以内。

---

## 4. 关键 API 注意点（通用 AscendC 层面）

- `DataCopy` 的源/目的基址通常要求 32 字节对齐；逐行小拷贝时若每行宽度（`statWidth`）或行间距导致非对齐，须改用 `DataCopyPad` 或调整 layout 以满足对齐，否则触发对齐异常。
- 逐行循环 DataCopy 的 `stride`/`blockLen` 参数须与 GM layout 的实际步长一致；若 GM 在该维度连续，可合并为更少、更大的整块 DataCopy 以进一步降低 MTE2 启动数（额外优化点，非必需）。
- `SetWaitFlag<HardEvent::MTE2_V>` 用于 MTE2→V 的依赖；仅在真正发起 GM→UB 拷贝的路径上需要。
- `TBuf<TPosition::VECCALC>` 用于声明 VECCALC 阶段的持久 UB buffer；`Get<T>()` 获取 `LocalTensor` 视图后通过偏移访问各分区。
- 跨 pipe 的 buffer 复用（ReinterpretCast）须确认源/目的在同一 pipe，否则需补跨 pipe 同步。

---

## 5. 实施步骤

1. **证明不变性**：逐行核查被搬运统计量的 GM 偏移公式，确认其不含外层循环索引（记录公式作为依据）。
2. **分配持久 UB buffer**（`TBuf<TPosition::VECCALC>`），容量 = 完整不变范围 × 统计量宽度 × sizeof(元素)；用 ascend-hardware 的真实 UB 容量更新 UB 预算注释。
3. **接入外层迭代计数器**：若其在签名中被忽略，删除忽略语句使其在函数体内可用。
4. **计算分区偏移**：在搬运点处的子索引循环体内、搬运判断之前，计算 `partitionOffset = subIndex * statWidth`，以及第二类统计量的分区基址。
5. **用首次迭代条件包裹原搬运循环**，DataCopy 目的地址改为分区偏移后的 UB 地址；MTE2→V 等待保留在条件块内。
6. **将下游对统计量的引用**统一改为指向持久 UB buffer 的分区偏移地址。
7. **迁移被取代 buffer 的借用临时量**到其他已完成使命的 UB 区域（同 pipe 优先），确认无需新增跨 pipe 同步。
8. **审查并仅删除为被取代 buffer 而存在的跨 pipe 同步**；为其他 pipe 交互存在的同步须保留。
9. **精度验证**：先跑外层迭代数 = 1 的 shape（回归首次路径），再跑外层迭代数 > 1 的 shape（验证缓存复用路径）。

---

## 6. LLM 前置问题

实施前必须回答：

1. 被搬运统计量的 GM 偏移公式是否可证明不含外层循环索引（或任何与之相关的维度）？
2. 外层迭代计数器是否已在搬运点可用且未被忽略？
3. 新增持久 UB 后，用真实芯片 UB 容量核算，总占用是否仍在上限以内？
4. 分区数 × 每批缓存大小是否恰好等于分配容量？（各分区无重叠、无越界，覆盖完整不变范围）
5. 原实现中是否有临时量借用了被取代 buffer 的尾部空间？若有，迁移到何处、是否同 pipe？
6. 当前存在哪些跨 pipe 同步？其中哪些是仅为被取代 buffer 而设、可安全删除？哪些必须保留？

---

## 7. 验收标准

正确性：

- 全量精度测试通过，**尤其外层迭代数 > 1 的 shape**（缓存复用路径被激活的 shape）。
- 外层迭代数 = 1 的 shape 结果与修改前一致（首次路径回归验证）。
- 多轮 task（大 batch、多 head 等大范围索引）下结果稳定，无随机 NaN 或 mismatch。

性能（定性，不含历史数字）：

- MTE2 时间下降；下降幅度随外层迭代数增大而增大（外层迭代数越大，省下的重复 MTE2 启动越多）。
- 标量/MTE2 启动控制开销进一步降低。
- task duration 改善方向正确；由于被缓存搬运占整体比例有限，整体收益为「定性正向」而非固定百分比。

## 检索卡（短卡）

动作：将循环不变统计量缓存在持久UB中，跨外层迭代复用，消除重复GM搬运。
适用：外层循环实际迭代超过一次，且统计量GM地址公式可证明不含该循环索引。
限制：缓存区须按统计量的不变维度分区，并覆盖完整不变范围。
范围：kernel外层循环中的逐行或逐组统计量。
检索词：循环不变量、统计量、GM地址公式、外层循环索引、持久UB buffer。
机会：outerCount大于1，循环不变统计量却在各次外层迭代重复搬运。
