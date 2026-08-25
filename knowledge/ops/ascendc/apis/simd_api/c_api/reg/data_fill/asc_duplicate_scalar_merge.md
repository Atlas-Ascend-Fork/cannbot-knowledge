---
type: API
title: AscDuplicateScalarMerge
description: merge模式下将标量值value广播到dst中被mask筛选的位置，未被筛选的元素保留原值。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_fill/asc_duplicate_scalar_merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscDuplicateScalarMerge

merge模式下，将标量值value广播到dst中被mask筛选的位置，dst中未被mask筛选的元素保留原值。

参数：dst(输入/输出): 目的操作数（矢量数据寄存器）。merge模式下，未被mask筛选的元素保留原值。；value(输入): 源操作数（标量）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Muls（灵活标量位置）](../../../basic_api/memory_vector_compute/basic_arithmetic/muls_flexible_scalar.md)（`related`）：Muls（灵活标量位置） 与《AscDuplicateScalarMerge》的实质衔接是：灵活标量 Muls 的 scalarTensorIndex、LocalTensor 单点标量和 cyclic-repeat 语义会直接影响广播乘法、量化 scale 与标量位置。
- [AscDuplicateHighest](asc_duplicate_highest.md)（`same_topic`）：AscDuplicateHighest 与《AscDuplicateScalarMerge》的实质衔接是：AscDuplicateHighest 从 src 最高 lane 广播到 mask 选中位置；Merge/Scalar/普通 Duplicate 的来源与未选中位置处理不同，相关错例直接约束枚举、范围和归约结果广播。
- [AscDuplicateMerge](asc_duplicate_merge.md)（`same_topic`）：ScalarMerge 使用标量源，按源形态选择。
- [AscDuplicateScalar](asc_duplicate_scalar.md)（`same_topic`）：AscDuplicateScalar 与《AscDuplicateScalarMerge》的实质衔接是：AscDuplicateScalar 把一个 scalar 广播到 RegTensor；Merge/Highest/普通 Duplicate 改变未选中 lane 或来源，标量运算和错例直接约束广播范围与消费方式。
<!-- cannbot:related:end -->
