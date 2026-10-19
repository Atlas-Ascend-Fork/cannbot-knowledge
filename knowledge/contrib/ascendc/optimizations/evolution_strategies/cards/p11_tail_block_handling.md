---
type: Optimization
title: 'P11: Tail Block Handling (尾块与边界处理)'
description: 参考实现精心设计了尾块处理机制以解决数据量不能被核心数整除的问题：1) 双轨制计算：同时计算正常核（normCoreHandleDefaultValues/normCoreHandleSparses）和尾核（tailCoreHandleDefaultValues/tailCoreHandleSpar…
tags:
- task.optimization
- topic.compute.indexing
- topic.implementation.tiling
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P11_tail_block_handling.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P11: Tail Block Handling (尾块与边界处理)

## 核心思想
参考实现精心设计了尾块处理机制以解决数据量不能被核心数整除的问题：1) 双轨制计算：同时计算正常核（normCoreHandleDefaultValues/normCoreHandleSparses）和尾核（tailCoreHandleDefaultValues/tailCoreHandleSparses）的处理数据量；2) 循环展开：正常循环使用defaultUbFactor批量处理，尾循环单独处理剩余数据；3) Loop/Tail分离：Host端计算normBlockLoop/tailBlockLoop和normBlockTailLoopSize/tailBlockTailLoopSize，Kernel端根据blockIdx_判断自己是正常核还是尾核。这种设计确保了在所有场景下都能实现近完美的负载均衡，避免了因数据量不是核心数倍而导致的性能损失。

## 代码骨架

// === 改造前（基线）===
```cpp
// 参考实现: 固定tile处理
for (uint32_t i = 0; i < this->innerLoops; i++) {
    CopyIn(i);
    Compute(i);
    CopyOut(i);
}
```

// === 改造后（优化实现）===
```cpp
// 参考实现: 余数处理
for (uint32_t i = 0; i < copyTimes; i++) {
    bool isRemainder = (i == copyTimes - 1 && copyTimesRemainder > 0);
    uint32_t tempDataCount = isRemainder ? copyTimesRemainder : Base::maxDataCount;
    if (isRemainder) {
        DataCopyExtParams copyParams{1, static_cast<uint32_t>(dataCount * sizeof(T)), 0, 0, 0};
        DataCopyPadExtParams<T> padParams{false, 0, 0, 0};
        DataCopyPad(dataLocal, inTensorsGM[...], copyParams, padParams);
    } else {
        DataCopy(dataLocal, inTensorsGM[...], dataCount);
    }
}
```

## 关键修改点

1. 预期收益: 保证数据安全性，避免越界访问，同时主循环保持高效; 确保所有边界情况下的计算正确性

## 常见陷阱

⚠️ AtomicAdd操作有一定性能开销
⚠️ 需要使用额外的tmpPattern buffer
⚠️ 需要预计算和存储kernel索引，增加UB使用

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
