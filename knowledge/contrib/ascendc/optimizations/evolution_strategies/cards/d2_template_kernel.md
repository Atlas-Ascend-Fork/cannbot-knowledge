---
type: Optimization
title: 'D2: Template Kernel Type Dispatch (模板化内核类型分发)'
description: 参考实现通过C++模板机制实现了对多种数据类型的统一支持。
tags:
- task.optimization
- paradigm.elementwise
- topic.compute.normalization
- topic.compute.composite
- topic.programming_model.execution_unit.scalar
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/120ae95ac453606fe8eb69a5d1662382d30fc315/community/ops/evolution-strategies/references/cards/D2_template_kernel.md
  role: primary
created_at: '2026-10-09T00:00:00Z'
updated_at: '2026-10-09T00:00:00Z'
platforms:
- a2
---

# D2: Template Kernel Type Dispatch (模板化内核类型分发)

## 核心思想
参考实现通过C++模板机制实现了对多种数据类型的统一支持。在Kernel端，SparseToDenseSimt类使用三个模板参数：IDX_T（indices数据类型）、Y_T（values/output数据类型）、COMP_T（内部计算使用的数据类型）。这种设计允许灵活组合不同的数据类型，如indices使用int32或int64，而values可以是float16、float32、bfloat16、int8~int64、bool等多种类型。Host端通过VALUE_DTYPE和INDICES_DTYPE集合进行严格的类型校验，确保只有支持的类型组合才能通过编译。这种设计不仅提高了算子的通用性，还为不同精度需求的场景提供了优化空间——例如在推理场景下可以使用float16减少内存带宽，在训练场景下使用float32保证精度。

## 代码骨架

// === 改造前（基线）===
```cpp
// 参考实现仅支持float32
AscendC::GlobalTensor<float> varGm;
AscendC::GlobalTensor<float> accumGm;
// ... 所有tensor都是float类型
```

// === 改造后（优化实现）===
```cpp
// 参考实现 - 模板化类型处理
template <typename U, typename T = float>
struct ApplyAdagradDUpdateSlots {
    using OpCopyInVar = Bind<Vec::CopyIn<U>, Placeholder::In0<U>>;
    using OpVarCast = Bind<Vec::Cast<T, U, 0>, OpCopyInVar>;
    // ... 在T类型上进行计算
};

// Tiling中针对不同类型的实例化
if (this->varDtype_ == ge::DT_FLOAT16) {
    eleBaseTiling.DoTiling<ApplyAdagradDOp::ApplyAdagradDUpdateSlots<half>::OpDag>(...);
} else if (this->varDtype_ == ge::DT_BF16) {
    eleBaseTiling.DoTiling<ApplyAdagradDOp::ApplyAdagradDUpdateSlots<bfloat16_t>::OpDag>(...);
}
```

## 关键修改点

1. 预期收益: 支持BF16/FP16/FP32三种数据类型，内存带宽节省50%(BF16)或25%(FP16)，同时通过FP32中间计算保持精度

## 常见陷阱

⚠️ 增加了模板代码复杂度，编译时间可能增加，需要为每种类型生成独立的二进制代码
⚠️ 增加了代码重复（两个DAG定义），需要更多编译时间生成多个模板实例
⚠️ 模板元编程增加编译时间；代码可读性降低

## 代码搜索关键词

```bash
grep -n "BUFFER_NUM\|InitBuffer\|TQue\|tileSize\|ubFactor\|Tiling\|BLOCK_DIM\|GetBlockNum" op_kernel/*.cpp op_host/*_tiling.cpp
```
