---
type: API
title: CountLeadingZero
description: 统计uint64_t数值二进制表示中前导0的个数，输入为0时返回64。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/CountLeadingZero.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# CountLeadingZero

头文件路径为："basic_api/kernel_operator_scalar_intf.h"。

统计uint64_t类型数值的二进制表示中前导0的个数（二进制表示中最高有效位到第一个'1'的'0'的数量，输入为0时返回64）。

以如下CountLeadingZero调用为例
其计算结果如下图所示

参数：valueIn(输入): 被统计的二进制数字。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetBitCount](get_bit_count.md)（`related`）：GetBitCount 与《CountLeadingZero》的实质衔接是：GetBitCount 对 countValue=1/0 分别对应 C API 的 asc_popc 与 AscZeroBitsCnt；CountLeadingZero 只统计最高位起连续零，可作为区分“全部位计数”和“前导计数”的直接边界。
- [__clz（整数数学函数）](../../../simt_api/math_functions/integer_math_functions/_clz.md)（`related`）：Basic API CountLeadingZero 对 uint64_t 定义输入为零时返回 64，补充另一接口层的边界语义。
- [asc_ffz（标量计算）](../../c_api/scalar_compute/asc_ffz.md)（`related`）：CLZ 从高位统计前导零，而 FFZ 返回首个零位置；选择取决于扫描方向和结果语义。
- [AscZeroBitsCnt](../../c_api/scalar_compute/asc_zero_bits_cnt.md)（`same_topic`）：AscZeroBitsCnt 与《CountLeadingZero》的实质衔接是：AscZeroBitsCnt 是 64 位零位计数；GetBitCount/popc、前导零和 ffz 提供总位数/零位置的邻近位操作，用于避免把计数与定位混淆。
- [CountBitsCntSameAsSignBit](count_bits_cnt_same_as_sign_bit.md)（`same_topic`）：《CountBitsCntSameAsSignBit》说明统计int64_t数值二进制表示中从最高数值位开始与符号位相同的连续比特位个数。；《CountLeadingZero》说明统计uint64_t数值二进制表示中前导0的个数，输入为0时返回64。。二者在符号位连续计数本质是有符号前导位分析，与CountLeadingZero、asc_clz和ZeroBitsCnt的位宽/符号合同直接相邻上存在可执行的直接衔接。
- [asc_clz（标量计算）](../../c_api/scalar_compute/asc_clz.md)（`same_topic`）：CountLeadingZero 与 asc_clz 都统计 uint64_t 从最高位到首个 1 的前导零数；它们是 C++ Basic 与 C 标量入口的直接对应。
- [接口变更说明（附录）](../../../appendix/interface_change_description.md)（`same_topic`）：focal 正文实际完整描述 CountLeadingZero 的输入、返回和支持平台，因此与独立接口卡语义重合。
<!-- cannbot:related:end -->
