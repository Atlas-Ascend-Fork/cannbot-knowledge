---
type: Optimization
title: 'P6: Multi-Algorithm Adaptive Selection (多算法自适应选择)'
description: Welford算法是BatchNorm训练场景的核心算法，相比传统的两遍计算（先算均值再算方差），Welford算法单次遍历即可同时得到均值和方差，且数值稳定性更好。
tags:
- task.optimization
- topic.compute.composite
- topic.memory
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/a2_welford_algorithm
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P6_multi_algo_selection.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- a2
---

# P6: Multi-Algorithm Adaptive Selection (多算法自适应选择)

> ⚠️ **已废弃**：标题 'Multi-Algorithm Adaptive Selection' 与内容不符——正文实为 Welford 算法，与 A2 重复。**去向**：[A2: Welford Algorithm](a2_welford_algorithm.md)。


## 核心思想
Welford算法是BatchNorm训练场景的核心算法，相比传统的两遍计算（先算均值再算方差），Welford算法单次遍历即可同时得到均值和方差，且数值稳定性更好。参考实现针对昇腾硬件特点进行了深度优化：1）并行Welford更新：WelfordParallelUpdate函数使用向量化指令同时更新多个通道的均值和M2（方差累计量）；2）分阶段归约：对于大规模数据，先在各分块上进行Welford更新，再通过WelfordParallelFinalize系列函数进行跨分块归约，支持R0/R1两个维度的灵活切分；3）二分累加优化：FullAichotomizeAdd实现了非二次幂长度的二分累加，先处理差值部分再进行标准二分归约，充分利用Vector Unit的并行能力。

## 代码骨架

// === 改造前（基线）===
```cpp
AscendC::ReduceSum(tempLocal, tempLocal, sharedLocal, tileLength);
float tileSum = tempLocal.GetValue(0);
```

// === 改造后（优化实现）===
```cpp
__aicore__ inline void ReduceMaxInplace(const LocalTensor<float>& srcLocal, int32_t count) {
    uint64_t repsFp32 = count >> 6;       // count / 64
    uint64_t remsFp32 = count & 0x3f;     // count % 64
    if (likely(repsFp32 > 1)) {
        Max(srcLocal, srcLocal[ELEM_PER_REP_FP32], srcLocal, ELEM_PER_REP_FP32, repsFp32 - 1, {1, 1, 1, 0, 8, 0});
        PipeBarrier<PIPE_V>();
    }
    if (unlikely(remsFp32 > 0)) {
        Max(srcLocal, srcLocal[offsetsFp32], srcLocal, remsFp32, 1, {1, 1, 1, 0, 8, 0});
        PipeBarrier<PIPE_V>();
    }
    WholeReduceMax(srcLocal, srcLocal, mask, 1, 8, 1, 8);
    PipeBarrier<PIPE_V>();
}
```

## 关键修改点

1. 用细粒度同步替代粗粒度 SyncAll
2. 预期收益: 大数据量场景下性能提升显著，减少同步开销

## 常见陷阱

⚠️ 代码复杂度增加，需要处理非64对齐的边界情况
⚠️ 算法理解难度较高；Welford更新需要更多中间变量
⚠️ 需要维护两套实现代码

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|SyncAll\|PipeBarrier\|ExecuteTask\|PRELOAD\|tileSize" op_kernel/*.cpp op_host/*_tiling.cpp
```
