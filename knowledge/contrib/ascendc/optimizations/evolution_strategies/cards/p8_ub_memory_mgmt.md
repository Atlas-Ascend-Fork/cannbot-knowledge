---
type: Optimization
title: 'P8: UB Memory Partitioning (UB内存分区管理)'
description: 在有限 UB 容量下为多个 tensor 合理分配空间：按 32B 对齐计算 buffer 大小、按生命周期合并/复用 buffer、溢出时缩减 tileSize 或降级 BUFFER_NUM，消除 UB overflow 并释放空间给更大 tile 或双缓冲。
tags:
- task.optimization
- topic.compute.composite
- topic.data_movement.memory_access
- topic.implementation.pipeline
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P8_ub_memory_mgmt.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P8: UB Memory Partitioning (UB内存分区管理)

## 核心思想
在有限 UB 容量下为多个 tensor 合理分配空间：按 32B 对齐计算 buffer 大小、按生命周期合并/复用 buffer、溢出时缩减 tileSize 或降级 BUFFER_NUM，消除 UB overflow 并释放空间给更大 tile 或双缓冲。它不改变数学逻辑，只调整 buffer 大小、数量和分配顺序。按 UB 占用比例分三种形态处理：α（占用 ≤ 50%，仅做 32B 对齐消除 bank conflict）、β（50-80%，缩减 tileSize 或合并生命周期不重叠的 buffer 做 zone 复用，见 P85）、γ（> 80% 或编译报 UB overflow，必须改分区方案：减半 tileSize / 降 BUFFER_NUM / 大中间结果搬 GM workspace / zone 复用）。

## 代码骨架

// === 改造前（独立分配，UB 紧张）===
```cpp
constexpr int32_t BUFFER_NUM = 1;
uint32_t tileSize = 4096;                       // fp16: 8KB per buffer
pipe.InitBuffer(inQueue,  BUFFER_NUM, tileSize * sizeof(T));
pipe.InitBuffer(outQueue, BUFFER_NUM, tileSize * sizeof(T));
pipe.InitBuffer(tmpQueue, BUFFER_NUM, tileSize * sizeof(T));
pipe.InitBuffer(maskQueue, BUFFER_NUM, tileSize * sizeof(T));   // 总 UB = 32KB
```

// === 改造后（缩减 tileSize + 32B 对齐 + zone 复用）===
```cpp
constexpr int32_t BUFFER_NUM = 2;               // 配合 P1 双缓冲
uint32_t tileSize = 2048;                       // tileSize 减半回到安全区
uint32_t bufSize = (tileSize * sizeof(T) + 31) & ~31;   // 向上 32B 对齐
pipe.InitBuffer(inQueue,  BUFFER_NUM, bufSize);
pipe.InitBuffer(outQueue, BUFFER_NUM, bufSize);
// tmp 和 mask 生命周期不重叠 → 合并为同一块 zone 复用（见 P85）
pipe.InitBuffer(sharedQueue, BUFFER_NUM, bufSize);      // 总 UB = 24KB
```

## 关键修改点

1. 单 buffer 大小 = `((tileSize × sizeof(dtype)) + 31) & ~31`（32B 对齐），总 UB 占用 = Σ（单 buffer × BUFFER_NUM）≤ UB_TOTAL × 0.8（留 20% 给栈与编译器临时变量）
2. tileSize / BUFFER_NUM 等分区决策放在 host tiling，禁止 kernel 内硬编码裸数字（`InitBuffer(q, 1, 8192)` 是反模式）
3. 形态 β/γ 优先合并生命周期不重叠的 buffer（zone reuse，见 P85），其次缩减 tileSize；tileSize < 128B 时 DataCopy 粒度太小，应改用 zone reuse
4. 已应用 P1 双缓冲（BUFFER_NUM=2）时 UB 翻倍，优先用 zone reuse 替代独立 buffer，仍溢出再考虑放弃双缓冲

## 常见陷阱

⚠️ buffer size 未 32B 对齐 → UB bank conflict，改 `((size + 31) & ~31)` 或 `AlignCeil(size, 32)`
⚠️ zone reuse 的 offset 区间 `[offset, offset+size)` 相交 → 运行时数据错乱
⚠️ 瓶颈不是 ub_memory_pressure 时 P8 无收益（UB 利用率已低），换瓶颈对应策略

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
