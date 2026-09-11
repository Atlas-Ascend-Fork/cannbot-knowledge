---
type: API
title: SetAtomicType
description: 通过模板参数设定后续原子操作的数据类型。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.atomic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
source_headers:
- include/basic_api/kernel_operator_set_atomic_intf.h
---

# SetAtomicType<a name="ZH-CN_TOPIC_0000001835083633"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_set_atomic_intf.h"`。

通过设置模板参数来设定原子操作不同的数据类型。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void SetAtomicType()
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
|--------|------|
| T | 设定原子操作不同的数据类型。 |

## 数据类型


- Ascend 950PR/Ascend 950DT，支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。



- Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。



- Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。



- Atlas 200I/500 A2 推理产品，支持的数据类型为int16_t、half、int32_t、float。



- Atlas 推理系列产品AI Core，支持的数据类型为int16_t、half、float。


## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- [SetAtomicAdd](set_atomic_add.md)、[SetAtomicMax](set_atomic_max_isasi.md)、[SetAtomicMin](set_atomic_min_isasi.md)内部已集成与SetAtomicType相同的功能。建议调用上述接口时，通过设置模板参数显式指定原子操作的数据类型，无需额外调用SetAtomicType接口。
- 使用完成后，建议使用DisableDmaAtomic清空原子操作的状态，以免影响后续相关指令功能。

## 调用示例<a name="section177231425115410"></a>

根据约束说明可知，使用[SetAtomicAdd](set_atomic_add.md)、[SetAtomicMax](set_atomic_max_isasi.md)、[SetAtomicMin](set_atomic_min_isasi.md)时，已通过模板参数指定原子操作的数据类型，无需额外调用`SetAtomicType`接口，因此本接口不提供调用示例。


<!-- cannbot:related:start -->
## 相关

- [DisableDmaAtomic](disable_dma_atomic.md)（`same_topic`）：函数原型：template <typename T> __aicore__ inline void SetAtomicType(AtomicType atomicType)。模板参数T指定数据类型。参数：atomicType为原子操作类型枚举。约束：与DisableDmaAtomic配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。 调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。 SetAtomicType 选择随路原子类型，DisableDmaAtomic 在使用后清状态，避免后续搬运继续执行原子操作。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 3 / 3 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [BlockSparseAttentionGrad 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicType(...)` 的直接调用（第 422 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc35/cube_op.h#L422)
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicType(...)` 的直接调用（第 2634 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch22/flash_attention_score_grad_s1s2_bn2gs1s2_sab.h#L2634)
- [FlashAttentionUnpaddingScoreGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_unpadding_score_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicType(...)` 的直接调用（第 2634 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch22/flash_attention_score_grad_s1s2_bn2gs1s2_sab.h#L2634)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
