---
type: API
title: asc_clz（标量计算）
description: 计算一个uint64_t类型整数在二进制表示下的前导零个数，即从二进制最高位开始，到第一个出现二进制1为止，中间连续的0的数量。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_clz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_clz（标量计算）

计算一个uint64_t类型整数在二进制表示下的前导零个数，即从二进制最高位开始，到第一个出现二进制1为止，中间连续的0的数量。
函数原型：int64_t asc_clz(uint64_t value_in)
返回值：反馈value_in的前导0的个数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [AscClearNthbit](asc_clear_nthbit.md)（`related`）：ClearNthBit 需要正确位编号，AscClz 等位查询可用于构造位置和验证结果，但不执行更新。
- [AscSflbits](asc_sflbits.md)（`related`）：AscSflbits 统计有符号数除符号位外的连续符号扩展位，asc_clz 统计 uint64 的前导零；对正数可用于位宽判断，但负数及 0/-1 的返回约定不同。
- [AscZeroBitsCnt](asc_zero_bits_cnt.md)（`related`）：asc_clz（标量计算） 与《AscZeroBitsCnt》的实质衔接是：asc_clz、__clz 与 CountLeadingZero 都求前导零；符号位连续计数、总位数和零位计数入口给出相邻位统计语义，便于避免替换时混淆。
- [CountBitsCntSameAsSignBit](../../basic_api/scalar_compute/count_bits_cnt_same_as_sign_bit.md)（`related`）：asc_clz（标量计算） 与《CountBitsCntSameAsSignBit》的实质衔接是：asc_clz、__clz 与 CountLeadingZero 都求前导零；符号位连续计数、总位数和零位计数入口给出相邻位统计语义，便于避免替换时混淆。
- [GetBitCount](../../basic_api/scalar_compute/get_bit_count.md)（`related`）：asc_clz（标量计算） 与《GetBitCount》的实质衔接是：asc_clz、__clz 与 CountLeadingZero 都求前导零；符号位连续计数、总位数和零位计数入口给出相邻位统计语义，便于避免替换时混淆。
- [__clz（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/_clz.md)（`related`）：C Scalar asc_clz 提供同一前导零计数，可用于 SIMT 与 SIMD Scalar 接口之间迁移。
- [CountLeadingZero](../../basic_api/scalar_compute/count_leading_zero.md)（`same_topic`）：CountLeadingZero 与 asc_clz 都统计 uint64_t 从最高位到首个 1 的前导零数；它们是 C++ Basic 与 C 标量入口的直接对应。
<!-- cannbot:related:end -->
