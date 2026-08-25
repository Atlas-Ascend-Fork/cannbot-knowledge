---
type: API
title: AscZeroBitsCnt
description: 获取一个uint64_t类型数字的二进制中0的个数。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_zero_bits_cnt.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscZeroBitsCnt

获取一个uint64_t类型数字的二进制中0的个数。
函数原型：int64_t asc_zero_bits_cnt(uint64_t value)
参数：value（输入）：被统计的二进制数字。
返回值：value中0的个数。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [CountBitsCntSameAsSignBit](../../basic_api/scalar_compute/count_bits_cnt_same_as_sign_bit.md)（`related`）：《CountBitsCntSameAsSignBit》说明统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。；《AscZeroBitsCnt》说明获取一个uint64_t类型数字的二进制中0的个数。。二者在符号位连续计数本质是有符号前导位分析，与CountLeadingZero、asc_clz和ZeroBitsCnt的位宽/符号合同直接相邻上存在可执行的直接衔接。
- [asc_clz（标量计算）](asc_clz.md)（`related`）：asc_clz（标量计算） 与《AscZeroBitsCnt》的实质衔接是：asc_clz、__clz 与 CountLeadingZero 都求前导零；符号位连续计数、总位数和零位计数入口给出相邻位统计语义，便于避免替换时混淆。
- [CountLeadingZero](../../basic_api/scalar_compute/count_leading_zero.md)（`same_topic`）：AscZeroBitsCnt 与《CountLeadingZero》的实质衔接是：AscZeroBitsCnt 是 64 位零位计数；GetBitCount/popc、前导零和 ffz 提供总位数/零位置的邻近位操作，用于避免把计数与定位混淆。
- [GetBitCount](../../basic_api/scalar_compute/get_bit_count.md)（`same_topic`）：GetBitCount 与《AscZeroBitsCnt》的实质衔接是：GetBitCount 对 countValue=1/0 分别对应 C API 的 asc_popc 与 AscZeroBitsCnt；CountLeadingZero 只统计最高位起连续零，可作为区分“全部位计数”和“前导计数”的直接边界。
- [asc_ffz（标量计算）](asc_ffz.md)（`same_topic`）：AscZeroBitsCnt 与《asc_ffz（标量计算）》的实质衔接是：AscZeroBitsCnt 是 64 位零位计数；GetBitCount/popc、前导零和 ffz 提供总位数/零位置的邻近位操作，用于避免把计数与定位混淆。
- [asc_popc（标量计算）](asc_popc.md)（`same_topic`）：AscZeroBitsCnt 与《asc_popc（标量计算）》的实质衔接是：AscZeroBitsCnt 是 64 位零位计数；GetBitCount/popc、前导零和 ffz 提供总位数/零位置的邻近位操作，用于避免把计数与定位混淆。
<!-- cannbot:related:end -->
