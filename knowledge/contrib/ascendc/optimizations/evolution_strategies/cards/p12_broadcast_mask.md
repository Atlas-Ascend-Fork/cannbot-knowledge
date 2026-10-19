---
type: Optimization
title: 'P12: Broadcast & Mask Operations (广播与掩码操作)'
description: 参考实现使用SelectWithBytesMask高阶API实现mask应用，替代手动if-else或Add操作。
tags:
- task.optimization
- topic.data_movement.memory_access
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/P12_broadcast_mask.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# P12: Broadcast & Mask Operations (广播与掩码操作)

## 核心思想
参考实现使用SelectWithBytesMask高阶API实现mask应用，替代手动if-else或Add操作。该API的语义是：当mask对应位置为true时，dst取value；否则取src。这种设计正好符合scaled masked softmax的需求：mask为true的位置应该被替换为MASK_VAL（-10000.0），这是一个极小的值，在softmax中会变成接近0的概率。相比参考实现中使用Add操作（要求mask是float类型且值为0/-inf），这种bool mask方式更加内存高效（1字节 vs 4字节）且语义清晰。

## 代码骨架

// === 改造前（基线）===
```cpp
// 参考实现 - 标量直接使用
lrScalar = lrGm.GetValue(0);
AscendC::Muls(lrMulGradLocal, gradLocal, this->lrScalar, this->tileSize);
```

// === 改造后（优化实现）===
```cpp
// 参考实现 - 标量广播为向量
using OpCopyInLr = Bind<Vec::Duplicate<U>, Placeholder::In2<U, Placeholder::ScalarAttr<true>>>;
using OpLrCast = Bind<Vec::Cast<T, U, 0>, OpCopyInLr>;
using OpLrMulGrad = Bind<Vec::Mul<T>, OpGradCast, OpLrCast>;  // 向量-向量乘法
```

## 关键修改点

1. 预期收益: 统一的向量计算流程，更高的执行效率，更好的精度控制

## 常见陷阱

⚠️ 需要额外的广播操作，但通常可以被内存访问隐藏
⚠️ Host端需要额外的广播模式识别逻辑，增加代码复杂度
⚠️ 需要额外buffer，增加计算步骤

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
