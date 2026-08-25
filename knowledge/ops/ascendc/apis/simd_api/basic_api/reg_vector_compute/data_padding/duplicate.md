---
type: API
title: Duplicate
description: 将标量或源寄存器最低位元素广播到目的寄存器，支持Scalar和Tensor两种模式，可配合mask使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/data_padding/Duplicate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Duplicate

支持Scalar和Tensor两种模式
-   Scalar模式：将scalarValue广播到寄存器，并保存在dstReg中（如果有mask，则保存在dstReg中被mask筛选的位置）。
-   Tensor模式：将srcReg的最低位元素广播到寄存器，并保存在dstReg中被mask筛选的位置。

头文件："basic_api/reg_compute/kernel_reg_compute_vec_duplicate_intf.h"。

参数：T: 操作数数据类型。支持的数据类型请参考数据类型。；U: scalar的数据类型。支持的数据类型请参考数据类型。；mode: MaskMergeMode枚举类型，选择MERGING模式或ZEROING模式。 • ZEROING模式下，mask未筛选的元素在dstReg中置零。 • MERGING模式下，mask未筛选的元素在dstReg中保留dstReg原值。；pos: 默认为LOWEST，表示将srcReg中的最低位广播至dstReg（暂不支持其他取值）。；S: 目的操作数的RegTensor类型， 例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；scalarValue(输入): 源操作数。 类型为标量。；srcReg(输入): 源操作数。 类型为RegTensor。

支持数据类型：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e8m0_t、fp8_e5m2_t、fp8_e4m3fn_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、complex32、int64_t、uint64_t、complex64。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：Duplicate 广播枚举与模板顺序不兼容 与《Duplicate》的实质衔接是：Duplicate 的模板参数顺序由 MaskMergeMode 与接口支持矩阵决定，Duplicate 卡给出实际重载契约。
- [InitOutput GM 专用，UB 清零用 Duplicate](../../../../../runbooks/compilation/initoutput_gm_ub_duplicate.md)（`exemplifies`）：InitOutput GM 专用，UB 清零用 Duplicate 与《Duplicate》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：该卡用 Duplicate 把归约 lane0 广播到向量，展示其在归一化链中的正确消费位置。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](../../../../../runbooks/performance/duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`exemplifies`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《Duplicate》具体提供“将标量或源寄存器最低位元素广播到目的寄存器，支持Scalar和Tensor两种模式，可配合mask使用。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [AscDuplicate](../../../c_api/reg/data_fill/asc_duplicate.md)（`same_topic`）：C Reg API AscDuplicate 是 C++ Reg Duplicate 的直接对应入口。
- [AscDuplicateHighest](../../../c_api/reg/data_fill/asc_duplicate_highest.md)（`same_topic`）：AscDuplicateHighest 与《Duplicate》的实质衔接是：AscDuplicateHighest 从 src 最高 lane 广播到 mask 选中位置；Merge/Scalar/普通 Duplicate 的来源与未选中位置处理不同，相关错例直接约束枚举、范围和归约结果广播。
- [Duplicate](../../memory_vector_compute/data_padding/duplicate.md)（`same_topic`）：Memory Tensor Duplicate 与 Reg Duplicate 都执行标量广播，但输出载体与 mask 语义不同。
<!-- cannbot:related:end -->
