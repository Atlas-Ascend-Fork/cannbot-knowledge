---
type: Optimization
title: 'P9: Deterministic Output via Workspace (确定性输出)'
description: 在多核并行场景下，如果多个核同时更新同一权重行，由于执行顺序不确定，最终结果虽然是正确的（原子加），但浮点累加顺序不同可能导致微小差异（非结合性）。
tags:
- task.optimization
- topic.optimizer
- topic.implementation.tiling
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P9_deterministic_output.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-13T00:00:00Z'
platforms:
- a2
---

# P9: Deterministic Output via Workspace (确定性输出)

## 核心思想
在多核并行场景下，如果多个核同时更新同一权重行，由于执行顺序不确定，最终结果虽然是正确的（原子加），但浮点累加顺序不同可能导致微小差异（非结合性）。这在分布式训练中会导致不同节点的梯度不一致，影响收敛。确定性模式通过反向处理和边界检测解决这一问题：每个核从后向前处理自己的数据块；检测与前一个核的边界索引是否相同；如果相同，当前核跳过该索引，由前一个核处理；通过SyncAll保证全局顺序。

## 代码骨架

// === 改造前（多核直接写输出，竞争 + 顺序不定）===
```cpp
for (uint32_t i = startIdx; i < endIdx; i++) {
    AtomicAdd(outputGm[indicesGm[i]], gradGm[i]);  // 竞争写，顺序不确定
}
```

// === 改造后（per-core workspace → 固定顺序归并，形态 β 密集累加）===
```cpp
// Host 侧：分配 workspace = coreNum × outputSlice × sizeof(float)
Duplicate(accLocal, 0.0f, outputSlice);            // 1. UB 内局部累加，无竞争
for (uint32_t i = startIdx; i < endIdx; i++) {
    accLocal[indicesGm[i]] += gradGm[i];
}
DataCopy(workspaceGm + blockIdx * outputSlice, accLocal, outputSlice);  // 2. 各核写私有 slice
SyncAll();                                          // 等待所有核写完 workspace
if (blockIdx == 0) {                                // 3. 核 0 按固定顺序 0→1→2... 归并
    for (uint32_t c = 1; c < coreNum; c++) {
        Add(outLocal, outLocal, workspaceSlice[c], outputSlice);
    }
    DataCopy(outputGm, outLocal, outputSlice);
}
```

形态变体：α（稀疏索引重叠）可用反向扫描 + 边界去重替代 workspace；γ（双输出量化中间态）workspace stride 取 `2 × numLastDim`。详见 Playbook Step 3C。

## 关键修改点

1. Host 侧申请 workspace，大小 = `coreNum × outputSlice × sizeof(dtype)`，经 TilingData 传入 kernel
2. 每核只写自己的 slice（offset = `blockIdx × sliceSize`），严禁越界写其他核区域
3. `SyncAll` 必须在所有核完成 workspace 写入后、归并前执行，不可省略
4. 由核 0（或固定顺序）归并到最终输出，归并 buffer ≥ outputSlice 且 32B 对齐；outputSlice 超 UB 容量时分 tile 归并
5. 稀疏索引跨核重复率极低（<1%）时 workspace 开销可能超过收益，退化为形态 α

## 常见陷阱

⚠️ 增加GM访存，需要额外的Workspace内存
⚠️ 约5-10%的性能损失（边界检测和反向遍历的开销）
⚠️ 原子操作有一定性能开销，但这是正确性必需的

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|SyncAll" op_kernel/*.cpp op_host/*_tiling.cpp
```
