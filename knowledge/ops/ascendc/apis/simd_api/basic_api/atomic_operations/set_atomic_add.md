---
type: API
title: SetAtomicAdd
description: 对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.atomic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicAdd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
source_headers:
- include/basic_api/kernel_operator_set_atomic_intf.h
---

# SetAtomicAdd<a name="ZH-CN_TOPIC_0000001487536650"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_set_atomic_intf.h"`。

对后续目的地址为GM的数据搬运开启原子累加。原子累加过程：将待拷贝的内容和GM已有内容进行求和，然后将求和结果写入GM。SetAtomicAdd接口可通过模板参数设定不同的累加数据类型。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void SetAtomicAdd()
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
|--------|------|
| T | 设定不同的原子累加操作数据类型。 |

## 数据类型


- Ascend 950PR/Ascend 950DT，支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。



- Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。



- Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据类型为int8_t、int16_t、half、bfloat16_t、int32_t、float。



- Atlas 200I/500 A2 推理产品，支持的数据类型为int16_t、half、int32_t、float。



- Atlas 推理系列产品AI Core，支持的数据类型为int16_t、half、float。



- Atlas 训练系列产品，支持的数据类型为float。


## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>


- Ascend 950PR/Ascend 950DT，支持的数据通路为UB/L0C Buffer-\>GM。



- Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的数据通路为UB/L0C Buffer/L1 Buffer-\>GM。



- Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的数据通路为UB/L0C Buffer/L1 Buffer-\>GM。



- Atlas 200I/500 A2 推理产品，支持的数据通路为UB/L0C Buffer/L1 Buffer-\>GM。



- Atlas 推理系列产品AI Core，支持的数据通路为UB-\>GM。



- Atlas 训练系列产品，支持的数据通路为UB-\>GM。


- 累加操作完成后，建议通过[DisableDmaAtomic](disable_dma_atomic.md)关闭原子累加，以免影响后续相关指令功能。
- 该接口执行前不会自动清零GM数据。开发者需根据算子逻辑判断是否清零，如需清零，请在执行前手动完成。
- SetAtomicAdd内部已集成与[SetAtomicType](set_atomic_type.md)相同的功能。建议调用上述接口时，通过设置模板参数显式指定原子操作的数据类型，无需额外调用SetAtomicType接口。

## 调用示例<a name="section177231425115410"></a>

```cpp
AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;
AscendC::LocalTensor<T> srcLocal = ubAllocator.Alloc<T, SIZE>();

AscendC::DisableDmaAtomic();
AscendC::DataCopy(srcLocal, srcGlobal, SIZE);
AscendC::SetFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
AscendC::WaitFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
AscendC::SyncAll();

// 开启原子累加，将Unified Buffer（UB）数据原子累加到GM
AscendC::SetAtomicAdd<T>();
AscendC::DataCopy(dstGlobal, srcLocal, SIZE);

// 关闭原子累加
AscendC::DisableDmaAtomic();
```

完整样例请参考[DataMovementWithAtomicOperations样例](https://gitcode.com/cann/asc-devkit/blob/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/06_atomic/data_movement_with_atomic_operations/data_movement_with_atomic_operations.asc)。


<!-- cannbot:related:start -->
## 相关

- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。；设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。。SetAtomicAdd 开启随路原子累加，DisableDmaAtomic 在同一 DMA 搬运状态链末端关闭该模式，文档明确要求成对调用。
- [UnfoldGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/unfold_grad.md)（`related`）：UnfoldGrad 实现记录“普通与 second-axis body 都遵循 `CopyIn→可选 T1→FP32 Cast→transpose/rearrange/add→Atomic CopyOut`”；SetAtomicAdd 规定“后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。”。该 API 正是重叠窗口梯度写回的冲突合并机制。
- [关键特性说明（原子操作）](key_features.md)（`related`）：函数原型：__aicore__ inline void SetAtomicAdd<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；浮点数累加可能产生非确定性结果。头文件：basic_api/kernel_operator_atomic_intf.h。；非确定性计算产生的前提条件：原子操作类型为累加（最大值/最小值满足结合律不受影响）、数据类型为浮点数（整数加法满足结合律不受影响）、带随路原子操作的搬运指令达到3条及以上。。候选特性卡补全焦点接口何时出现非确定性以及如何规避。
- [AscSetAtomicAdd](../../c_api/atomic/datamove_atomic/asc_set_atomic_add.md)（`same_topic`）：设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。；本接口对后续目的地址为GM的数据搬运指令开启原子累加。两接口在 Basic API 和 C API 中设置同一后续 GM 搬运原子累加语义。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 47 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [ThreeInterpolateBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/cv/image/three_interpolate_backward.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 316 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/three_interpolate_backward/op_kernel/three_interpolate_backward.cpp#L316)
- [CircularPad2dBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_2d_backward.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 125 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/arch32/circular_pad_grad.h#L125)
- [IndexFill A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/index/index_fill.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 207 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/index_fill_base.h#L207)
- [BlockSparseAttentionGrad A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 160 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc22/attn_infra/gemm/block/block_mmad_bsag2.hpp#L160)
- [CircularPad3dBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/circular_pad_3d_backward.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 125 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/conversion/circular_pad_grad/op_kernel/arch32/circular_pad_grad.h#L125)
- [InplaceIndexFill A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_index_fill.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 207 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_kernel/index_fill_base.h#L207)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 239 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_stage2.h#L239)
- [AddLora A2 ACLNN 算子知识](../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 651 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/add_lora/op_kernel/add_lora_base.h#L651)
- [ChamferDistanceBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/loss/chamfer_distance_backward.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 136 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/loss/chamfer_distance_grad/op_kernel/chamfer_distance_grad.h#L136)
- [FlashAttentionScoreGrad 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attention_score_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `SetAtomicAdd(...)` 的直接调用（第 956 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch35/flash_attention_score_grad_block_vec.h#L956)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
