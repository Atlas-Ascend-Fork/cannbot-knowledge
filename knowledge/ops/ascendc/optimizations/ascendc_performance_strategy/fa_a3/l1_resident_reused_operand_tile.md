---
type: Optimization
title: 复用型矩阵操作数常驻 L1，跨微块减少 GM 搬运
description: 将每个输出微块内从GM加载的复用操作数tile改为跨微块常驻L1。
tags:
- task.optimization
- topic.attention
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/09-l1-resident-reused-operand-tile.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：复用型矩阵操作数常驻 L1，跨微块减少 GM 搬运

> **单一优化点：** 当矩阵阶段的某个输入 tile 会被同一 task 内多个 M/N 微块重复消费时，将该 tile 在进入微块循环前搬入 L1 并保持到所有消费者完成后再释放，避免每个微块重复 GM->L1 搬运。

本策略适用于各类 attention-like AscendC kernel 的矩阵阶段（含 GQA/MQA 与稀疏/反向变体）。典型对象包括 forward 的 V tile、backward 的 K/V/dO tile、多头潜空间类变体的 latent tile，或任何在同一归约 tile 内被多个输出微块复用的矩阵操作数。

---

## 1. 性能问题模式

低效模式：

```text
for output_micro_tile in M_or_N_tiles:
  for reduce_tile in K_tiles:
    load reused_operand_tile from GM to L1
    load per_micro_tile_operand from GM/workspace to L1
    L1 -> L0
    MMAD
```

如果 `reused_operand_tile` 与 `output_micro_tile` 无关，它会被重复搬运。优化后：

```text
for reduce_tile in K_tiles:
  load reused_operand_tile once into L1 cache

for output_micro_tile in M_or_N_tiles:
  for reduce_tile in K_tiles:
    reuse L1 cached operand
    load only per_micro_tile_operand
    L1 -> L0
    MMAD

release reused_operand_tile cache
```

收益来源：

- 减少 GM->L1 字节数。
- 减少 MTE2 搬运指令和地址计算。
- 降低 AIC 等待搬运完成的概率。
- 不改变 Cube FOPs。

---

## 2. 适用条件

必须同时满足：

| 条件 | 要求 |
|---|---|
| 操作数可复用 | 同一 task 内至少两个输出微块读取完全相同的 GM/L1 tile |
| 生命周期可界定 | 能明确第一个消费者之前加载、最后一个消费者之后释放 |
| 容量足够 | L1 能同时容纳缓存 tile、当前微块专属 tile 和原有队列/scratch |
| 地址稳定 | 缓存 tile 的 GM offset 不依赖正在遍历的输出微块 |
| 语义不变 | 不改变 MMAD 顺序、累加初始化、数据类型、转置/format 和尾块规则 |
| 测试稳定 | baseline 编译、精度和性能可重复 |

优先适用：

- 一个 reduce tile 被 2 个以上 M/N 微块消费。
- reused operand 的 GM->L1 搬运在 profiling 中占比可见。
- tile 数量固定且小，例如 2 个 K/V slice 被 4 个 M 微块复用。
- 当前实现每个微块都 `Alloc/Load/Free` 同一个 operand tile。

不适用：

- operand tile 随输出微块改变，无法跨微块复用。
- L1 容量不足，缓存后挤掉更关键的 double buffer。
- operand 只被消费一次。
- 缓存会改变 sparse/mask/dropout/causal 边界的有效数据范围。
- 为实现本策略必须改变分核、tile shape 或数学公式。

---

## 3. 识别方法

LLM/agent 实施前必须先回答：

```text
1. 哪个矩阵阶段存在重复 GM->L1？
2. 被缓存 operand 的 GM offset 是否与外层微块索引无关？
3. 每个 task 内该 operand 被复用几次？
4. L1 同时驻留的最大字节数是多少？
5. 哪个循环边界是安全加载点？
6. 哪个循环边界是安全释放点？
```

建议统计：

```text
old_load_count = output_micro_tile_count * reduce_tile_count
new_load_count = reduce_tile_count
saved_loads = old_load_count - new_load_count
saved_bytes = saved_loads * operand_tile_bytes
```

若 `saved_loads <= 0` 或 `saved_bytes` 小于测量噪声，不实施。

---

## 4. 改写模板

低效模式：

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

推荐模式：

```cpp
LocalTensor<T> rhsCache[MAX_REDUCE_TILES];

for (uint32_t k = 0; k < kCount; ++k) {
    rhsCache[k] = rhsQue.AllocTensor<T>();
    LoadRhsTile(rhsCache[k], task, k);
    rhsQue.EnQue(rhsCache[k]);
    rhsCache[k] = rhsQue.DeQue<T>();
}

for (uint32_t m = 0; m < mCount; ++m) {
    bool firstReduce = true;
    for (uint32_t k = 0; k < kCount; ++k) {
        auto lhsL1 = LoadLhsForMicroTile(task, m, k);
        if (!firstReduce) {
            PipeBarrier<PIPE_M>();
        }
        ComputeMmad(lhsL1, rhsCache[k], m, k, firstReduce);
        firstReduce = false;
        FreeLhsForMicroTile(lhsL1);
    }
}

for (uint32_t k = 0; k < kCount; ++k) {
    rhsQue.FreeTensor(rhsCache[k]);
}
```

若 `TQue` 不能安全持有多个已 `DeQue` 未 `Free` tensor，可改为 `TBuf<TPosition::A1/B1>` 静态切片，但必须显式补齐 HardEvent 生命周期；不要混用 TQue 的隐式同步语义和裸 TBuf。

---

## 5. 约束与禁止事项

必须：

- 保留每个 reduce tile 的尾块有效范围。
- 保留原 `cmatrixInitVal` 语义；只有第一个 reduce tile 初始化 L0C。
- 保留消费者完成前的 L1 生命周期。
- 保留原有跨 AIC/AIV 信号协议。
- 对 `sparse/causal/mask` 场景按真实有效 tile 加载，不读取越界 GM。

禁止：

- 不要把随微块变化的 operand 错当成可复用 tile。
- 不要为了缓存 operand 改变输出微块顺序，除非能证明累加语义等价。
- 不要在每个微块结束时释放 cached operand。
- 不要同时修改 workspace 槽数、全局流水、L0 TBuf 或同步删减。
- 不要只因小 case 通过就认为 L1 容量和生命周期安全。

---

## 6. 验收标准

正确性：

- 全量精度通过，包括 tail、mask、GQA/MQA head mapping、latent/head 维度映射、反向累加 case。
- 无 L1 overwrite、queue depth 不足、随机 hang。
- Cube FOPs 不增加。

性能：

- 目标 operand 的 GM->L1 次数下降到理论值。
- AIC MTE2 指令数或 GM->L1 字节数下降。
- Task Duration 不回退；若回退，检查 L1 容量压力、queue depth 和释放点。

建议记录：

```text
old_operand_loads_per_task
new_operand_loads_per_task
saved_gm_to_l1_bytes
AIC MTE2 instruction count
Cube time
Task Duration
```

## 检索卡（短卡）

动作：将每个输出微块内从GM加载的复用操作数tile改为跨微块常驻L1。
适用：同一task内至少两个输出微块读取完全相同的GM/L1 tile。
限制：L1驻留须覆盖全部消费者；保留尾块有效范围与cmatrixInitVal语义，仅首个reduce tile初始化。
范围：矩阵阶段单个task内跨M/N输出微块复用的输入tile。
检索词：复用操作数tile、L1常驻、输出微块、M/N tiles、reduce tile。
机会：同一task的多个M/N微块重复消费同一输入tile。
