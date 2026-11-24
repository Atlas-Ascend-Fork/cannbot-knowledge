---
type: Optimization
title: 固定生命周期 L0 TQue 改为 TBuf 双缓冲并显式 HardEvent 管理
description: 将固定ping-pong生命周期的L0临时tensor由TQue改为TBuf静态双缓冲。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/12-static-l0-tbuf-double-buffer.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：固定生命周期 L0 TQue 改为 TBuf 双缓冲并显式 HardEvent 管理

> **单一优化点：** 对热循环中尺寸固定、生产消费距离固定、不会动态排队的 L0A/L0B/L0C 临时 tensor，用 `TBuf` 静态双缓冲替换 `TQue AllocTensor/EnQue/DeQue/FreeTensor`，并用成对 HardEvent 显式表达 load/compute/fixpipe 生命周期，减少队列管理和隐式同步开销。

本策略适用于各类 attention-like AscendC kernel 的矩阵 micro-tile 热路径。它只适合 L0/L1 临时缓冲生命周期固定的场景，不适合真实需要队列深度、动态排队或跨阶段复杂交接的路径。

---

## 1. 原理

TQue 负责：

```text
AllocTensor -> producer writes -> EnQue -> DeQue -> consumer reads -> FreeTensor
```

它同时承担 buffer 管理、队列 token 和同步语义。若热循环中的 tensor 实际只有固定 ping-pong 生命周期，例如：

```text
slot 0 load -> MMAD consumes -> slot 0 reusable
slot 1 load -> MMAD consumes -> slot 1 reusable
```

则 TQue 的入队/出队和队列状态维护会变成额外开销。TBuf 只提供静态内存，不提供同步；因此替换时必须显式补齐：

```text
slot free event
slot ready event
consumer done event
```

收益来源：

- 删除热点循环中的 AllocTensor/EnQue/DeQue/FreeTensor。
- 减少队列状态维护和部分隐式同步。
- 使 slot 选择和生命周期更直接。
- 不改变 MMAD/Fixpipe/DataCopy 数学语义。

---

## 2. 适用条件

必须同时满足：

| 条件 | 要求 |
|---|---|
| 尺寸固定 | 每个 slot 的最大元素数可静态或 tiling 期确定 |
| 生命周期固定 | producer 和 consumer 距离固定，可用 1 或 2 个 slot ping-pong 表达 |
| 无动态排队 | 不存在连续多次生产但消费者延迟未知的情况 |
| 同步可显式表达 | 能列出每个 slot 的 free/ready/done HardEvent |
| 容量足够 | TBuf 总大小覆盖所有 slot 和最大 tail 对齐 |
| 基线稳定 | 原 TQue 路径精度稳定，便于替换后验证 |

优先适用：

- L0A/L0B：MTE1 load 后立即被 M 使用，使用后 slot 可覆盖。
- L0C/CO1：M 累加完成后 Fixpipe 读取，Fixpipe 完成后 slot 可覆盖。
- 每个 micro tile 重复执行 queue 操作，且 queue depth 固定为 1 或 2。

不适用：

- queue 跨多个异步阶段传递，消费者距离不固定。
- queue depth 用于吸收 producer/consumer 速率差。
- tensor 生命周期跨函数、跨 core 或跨未知 wrapper。
- 无法可靠申请和释放 event id。
- 替换会迫使删除必要同步或改变执行顺序。

---

## 3. TBuf 与 TQue 语义边界

硬规则：

```text
TBuf only manages memory.
TBuf does not EnQue.
TBuf does not DeQue.
TBuf does not provide producer-consumer sync.
TBuf does not know when a slot is free.
```

因此：

- 从 TQue 改为 TBuf 后，所有原本由 queue handoff 提供的 happens-before 必须显式重建。
- `Get<T>()` 返回同一块 buffer 的 base tensor；多 slot 需要手动切片。
- 不调用 `FreeTensor`；slot 可复用必须由 free event 保护。
- 不要把 `SetWaitFlag<HardEvent::X_Y>()` 当作长期 slot 生命周期，它只是一次即时屏障。

---

## 4. Buffer 布局模板

示例：

```cpp
static constexpr uint32_t L0_AB_SLOT_COUNT = 2;
static constexpr uint32_t L0_C_SLOT_COUNT = 2;
static constexpr uint32_t L0A_SLOT_ELEMS = BLOCK_M * BLOCK_K;
static constexpr uint32_t L0B_SLOT_ELEMS = BLOCK_K * BLOCK_N;
static constexpr uint32_t L0C_SLOT_ELEMS = BLOCK_M * BLOCK_N;

TBuf<TPosition::A2> l0ABuf;
TBuf<TPosition::B2> l0BBuf;
TBuf<TPosition::CO1> l0CBuf;

LocalTensor<T> l0A[L0_AB_SLOT_COUNT];
LocalTensor<T> l0B[L0_AB_SLOT_COUNT];
LocalTensor<float> l0C[L0_C_SLOT_COUNT];
```

初始化：

```cpp
pipe.InitBuffer(l0ABuf, L0_AB_SLOT_COUNT * L0A_SLOT_ELEMS * sizeof(T));
pipe.InitBuffer(l0BBuf, L0_AB_SLOT_COUNT * L0B_SLOT_ELEMS * sizeof(T));
pipe.InitBuffer(l0CBuf, L0_C_SLOT_COUNT * L0C_SLOT_ELEMS * sizeof(float));

auto aBase = l0ABuf.Get<T>();
auto bBase = l0BBuf.Get<T>();
auto cBase = l0CBuf.Get<float>();

for (uint32_t i = 0; i < L0_AB_SLOT_COUNT; ++i) {
    l0A[i] = aBase[i * L0A_SLOT_ELEMS];
    l0B[i] = bBase[i * L0B_SLOT_ELEMS];
}
for (uint32_t i = 0; i < L0_C_SLOT_COUNT; ++i) {
    l0C[i] = cBase[i * L0C_SLOT_ELEMS];
}
```

实际切片 API 按项目 AscendC 版本使用 `operator[]`、`SetAddrWithOffset` 或项目封装；不得用普通 C++ 指针替代 `LocalTensor`。

---

## 5. HardEvent 生命周期模板

### 5.1 L0A/L0B load -> MMAD

需要表达：

```text
M done with slot -> MTE1 may overwrite
MTE1 loaded slot -> M may read
```

模板：

```cpp
TEventID abFreeEvent[2];
TEventID abReadyEvent;

// init once
for each slot:
  abFreeEvent[slot] = pipe.AllocEventID<HardEvent::M_MTE1>();
  SetFlag<HardEvent::M_MTE1>(abFreeEvent[slot]);
```

热循环：

```cpp
uint32_t slot = abSlot;
WaitFlag<HardEvent::M_MTE1>(abFreeEvent[slot]);

LoadA(l0A[slot], ...);
LoadB(l0B[slot], ...);

SetWaitFlag<HardEvent::MTE1_M>();
Mmad(l0C[cSlot], l0A[slot], l0B[slot], ...);

SetFlag<HardEvent::M_MTE1>(abFreeEvent[slot]);
abSlot ^= 1;
```

说明：`SetWaitFlag<MTE1_M>` 可以用于一次 load->MMAD 屏障；slot free 必须使用持久 per-slot event。

### 5.2 L0C MMAD -> Fixpipe

需要表达：

```text
Fixpipe done with C slot -> M may overwrite
M done writing C slot -> Fixpipe may read
```

模板：

```cpp
TEventID cFreeEvent[2];

// init once
for each slot:
  cFreeEvent[slot] = pipe.AllocEventID<HardEvent::FIX_M>();
  SetFlag<HardEvent::FIX_M>(cFreeEvent[slot]);
```

热循环：

```cpp
uint32_t cSlot = cSlotId;
WaitFlag<HardEvent::FIX_M>(cFreeEvent[cSlot]);

for each reduce micro tile:
  if (!firstReduce) {
      PipeBarrier<PIPE_M>();
  }
  Mmad(l0C[cSlot], l0A[abSlot], l0B[abSlot], firstReduce);

SetWaitFlag<HardEvent::M_FIX>();
Fixpipe(dst, l0C[cSlot], ...);
SetFlag<HardEvent::FIX_M>(cFreeEvent[cSlot]);

cSlotId ^= 1;
```

禁止用单纯的 `SetWaitFlag<FIX_M>()` 替代 `cFreeEvent[cSlot]`。即时屏障不能表示“这个 C slot 已被 Fixpipe 释放”。

---

## 6. 实施步骤

1. 只选择一个 buffer 家族开始，例如先 L0A/L0B，再 L0C。
2. 记录原 TQue 的 `AllocTensor/EnQue/DeQue/FreeTensor` 路径和隐含同步。
3. 计算每个 slot 的最大元素数和对齐字节数。
4. 用 TBuf 一次性分配所有 slot，并手动切片。
5. 为每个可复用 slot 分配持久 free event。
6. 在生产者覆盖 slot 前 `Wait free`。
7. 在消费者完成后 `Set free`。
8. 对一次性 ready 关系使用 `SetWaitFlag` 或项目现有 wrapper，但必须确认 HardEvent 方向正确。
9. 编译、基础精度、全量精度、性能逐步验证。
10. 若任一步出现 hang 或性能大幅回退，回滚到上一个 buffer 家族，不要叠加修改。

---

## 7. 禁止事项

禁止：

- 不要在 TBuf 上调用 `AllocTensor/EnQue/DeQue/FreeTensor`。
- 不要删除原 TQue 后不补同步。
- 不要手写固定 event id；优先使用 `AllocEventID` 或项目安全封装。
- 不要省略 final drain：退出前必须等待并释放持久 event。
- 不要让 A/B slot 和 C slot 共享同一 event，除非 HardEvent 和生命周期完全相同。
- 不要同时改变 tile shape、workspace slot、全局任务流水或同步删减。
- 不要把性能回退归因于 TBuf 本身；优先检查是否用即时 barrier 串行化了 slot 生命周期。

---

## 8. 验收标准

正确性：

- 编译通过。
- 基础和全量精度通过。
- 连续压力运行无 hang、event mismatch、buffer overwrite。
- event id 申请和释放成对。

性能：

- 热循环中的目标 TQue queue 操作消失。
- AIC scalar time 或 queue overhead 下降。
- Cube time 不明显增加。
- Task Duration 至少不回退；若回退，检查是否把 per-slot free event 写成了即时 `SetWaitFlag`。

建议记录：

```text
removed_alloc_enque_deque_free_count
TBuf bytes per position
persistent_event_count
AIC scalar time
Cube time
Fixpipe time
Task Duration
accuracy pass count
```

## 检索卡（短卡）

动作：将固定ping-pong生命周期的L0临时tensor由TQue改为TBuf静态双缓冲。
适用：每槽最大元素数可静态或tiling期确定，且生产者与消费者距离固定。
限制：仅限不会动态排队的临时tensor；替换时须覆盖原TQue承担的管理、token和同步语义。
范围：热循环内固定生命周期的L0A、L0B、L0C临时tensor。
检索词：TQue、TBuf、静态双缓冲、ping-pong、L0A、L0B、L0C。
机会：热循环中的tensor只按固定slot执行加载、MMAD消费与复用，却仍使用队列流程。
