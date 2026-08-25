---
type: API
title: AscDuplicateScalar
description: 将标量值value广播到dst寄存器，支持带mask和不带mask两种模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_fill/asc_duplicate_scalar.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscDuplicateScalar

将标量值value广播到dst寄存器中。支持带mask和不带mask两种模式
- 带mask模式：将value写入dst中被mask筛选的位置，未被筛选的位置被置为0。
- 不带mask模式：将value广播写入dst的全部位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：AscDuplicateScalar 与《Duplicate 广播枚举与模板顺序不兼容》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer](../../../../../runbooks/precision/count_based_max_min_is_element_wise_not_scalar_broadcast.md)（`exemplifies`）：AscDuplicateScalar 与《Max/Min 逐元素非标量广播 须 Duplicate 至同长 buffer》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：AscDuplicateScalar 与《Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [Muls（灵活标量位置）](../../../basic_api/memory_vector_compute/basic_arithmetic/muls_flexible_scalar.md)（`related`）：Muls（灵活标量位置） 与《AscDuplicateScalar》的实质衔接是：灵活标量 Muls 的 scalarTensorIndex、LocalTensor 单点标量和 cyclic-repeat 语义会直接影响广播乘法、量化 scale 与标量位置。
- [AscDuplicate](asc_duplicate.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicate》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [AscDuplicate](../../vector_compute/asc_duplicate.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicate》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [AscDuplicateHighest](asc_duplicate_highest.md)（`same_topic`）：AscDuplicateHighest 与《AscDuplicateScalar》的实质衔接是：AscDuplicateHighest 从 src 最高 lane 广播到 mask 选中位置；Merge/Scalar/普通 Duplicate 的来源与未选中位置处理不同，相关错例直接约束枚举、范围和归约结果广播。
- [AscDuplicateHighestMerge](asc_duplicate_highest_merge.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicateHighestMerge》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [AscDuplicateMerge](asc_duplicate_merge.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicateMerge》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
- [AscDuplicateScalarMerge](asc_duplicate_scalar_merge.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicateScalarMerge》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
<!-- cannbot:related:end -->
