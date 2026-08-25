---
type: API
title: LogicalNot
description: 按元素进行取反操作。当输入的数据类型不是bool时，零被视为False，非零数据被视为True。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/LogicalNot_interface/LogicalNot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LogicalNot

按元素进行逻辑取反操作。当输入数据类型不是bool时，零视为False，非零视为True。仅Ascend 950PR/950DT支持。

函数原型：template <const LogicalNotConfig& config = DEFAULT_LOGICAL_NOT_CONFIG, typename T, typename U> __aicore__ inline void LogicalNot(const LocalTensor<T>& dst, const LocalTensor<U>& src, const uint32_t count)

模板参数config为LogicalNotConfig类型，含isReuseSource（预留，传false）；T为目的操作数数据类型（仅支持bool）；U为源操作数数据类型（支持bool/int8_t/uint8_t/int16_t/uint16_t/half/bfloat16_t/int32_t/uint32_t/float/int64_t/uint64_t）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src为输入操作数；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [BitwiseNot](../bitwise_not_interface/bitwise_not.md)（`same_topic`）：LogicalNot 与《BitwiseNot》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
- [GetBitwiseNotMaxMinTmpSize](../bitwise_not_interface/get_bitwise_not_max_min_tmp_size.md)（`same_topic`）：LogicalNot 与《GetBitwiseNotMaxMinTmpSize》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
- [GetBitwiseNotTmpBufferFactorSize](../bitwise_not_interface/get_bitwise_not_tmp_buffer_factor_size.md)（`same_topic`）：LogicalNot 与《GetBitwiseNotTmpBufferFactorSize》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
- [GetLogicalNotMaxMinTmpSize](get_logical_not_max_min_tmp_size.md)（`same_topic`）：LogicalNot 与《GetLogicalNotMaxMinTmpSize》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
- [GetLogicalNotTmpBufferFactorSize](get_logical_not_tmp_buffer_factor_size.md)（`same_topic`）：LogicalNot 与《GetLogicalNotTmpBufferFactorSize》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
<!-- cannbot:related:end -->
