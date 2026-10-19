---
type: Optimization
title: 'P7: 32B Alignment + DataCopyPad (数据对齐与填充)'
description: 参考实现充分利用了Ascend C的向量化指令（如Adds、Cast、Duplicate等）进行高效计算。
tags:
- task.optimization
- topic.compute.indexing
- topic.programming_model.execution_unit.cube
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P7_data_alignment.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P7: 32B Alignment + DataCopyPad (数据对齐与填充)

## 核心思想
参考实现充分利用了Ascend C的向量化指令（如Adds、Cast、Duplicate等）进行高效计算。在foreach_add_scalar.cpp中，通过AddsAdapter函数包装Adds指令，实现了类型安全的高性能加法操作。对于BF16和FP16类型，参考实现采用FP32中间计算（通过Cast转换），然后使用RoundMode::CAST_RINT进行四舍五入，在保证精度的同时充分利用向量化指令的吞吐量。此外，参考实现使用了ListTensorDesc来描述tensor列表的内存布局，支持非连续存储的tensor（通过AutoContiguous标记在Host端处理）。参考实现虽然使用了Add和Duplicate指令，但没有考虑向量化对齐和数据类型转换优化。

## 代码骨架

// === 改造前（基线）===
```cpp
// 参考实现: 无对齐优化
AscendC::DataCopy(outputGm[tile_offset], outLocal, current_tile_size);
```

// === 改造后（优化实现）===
```cpp
// 参考实现: 32字节对齐优化
constexpr uint8_t ADDCDIV_LIST_BYTE_PER_BLOCK = 32;
if (uValue * sizeof(T) % ADDCDIV_LIST_BYTE_PER_BLOCK == 0) {
    DataCopy(dstLocal, tensor1Local, uValue);
} else {
    int32_t dataCountInBlock = ADDCDIV_LIST_BYTE_PER_BLOCK / sizeof(T);
    DataCopy(dstLocal, tensor1Local, (uValue + dataCountInBlock - 1) / dataCountInBlock * dataCountInBlock);
}
```

## 关键修改点

1. 预期收益: 提高内存访问效率，减少非对齐访问开销约5-10%; 最大化内存带宽利用率，提升数据拷贝效率

## 常见陷阱

⚠️ 需要复杂的参数计算
⚠️ 可能需要额外的内存开销用于对齐填充
⚠️ 需要额外计算stride参数

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
