---
type: API
title: CountBitsCntSameAsSignBit
description: 统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/CountBitsCntSameAsSignBit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CountBitsCntSameAsSignBit

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

统计int64_t类型数值的二进制表示中，从最高数值位开始与符号位相同的连续比特位的个数。

以如下CountBitsCntSameAsSignBit调用为例
其计算结果如下图所示

参数：valueIn(输入): 被统计的二进制数字。

约束：当输入是-1（比特位全1）或者0（比特位全0）时，返回-1。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [AscZeroBitsCnt](../../c_api/scalar_compute/asc_zero_bits_cnt.md)（`related`）：《CountBitsCntSameAsSignBit》说明统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。；《AscZeroBitsCnt》说明获取一个uint64_t类型数字的二进制中0的个数。。二者在符号位连续计数本质是有符号前导位分析，与CountLeadingZero、asc_clz和ZeroBitsCnt的位宽/符号合同直接相邻上存在可执行的直接衔接。
- [GetBitCount](get_bit_count.md)（`related`）：《CountBitsCntSameAsSignBit》说明统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。；《GetBitCount》说明统计uint64_t数值二进制表示中指定比特值（0或1）的出现次数。。二者在符号位连续计数本质是有符号前导位分析，与CountLeadingZero、asc_clz和ZeroBitsCnt的位宽/符号合同直接相邻上存在可执行的直接衔接。
- [asc_clz（标量计算）](../../c_api/scalar_compute/asc_clz.md)（`related`）：asc_clz（标量计算） 与《CountBitsCntSameAsSignBit》的实质衔接是：asc_clz、__clz 与 CountLeadingZero 都求前导零；符号位连续计数、总位数和零位计数入口给出相邻位统计语义，便于避免替换时混淆。
- [CountLeadingZero](count_leading_zero.md)（`same_topic`）：《CountBitsCntSameAsSignBit》说明统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。；《CountLeadingZero》说明统计uint64_t数值二进制表示中前导0的个数，输入为0时返回64。。二者在符号位连续计数本质是有符号前导位分析，与CountLeadingZero、asc_clz和ZeroBitsCnt的位宽/符号合同直接相邻上存在可执行的直接衔接。
<!-- cannbot:related:end -->
