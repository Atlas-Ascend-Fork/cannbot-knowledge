---
type: API
title: __ll2half_rna
description: 遵循CAST_ROUND模式，将int64类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__ll2half_rna.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2half_rna

功能：遵循CAST_ROUND模式，将int64类型数据转换为half类型数据，返回转换后的值。

函数原型：half __ll2half_rna(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_ROUND模式转换成的half类型数据。本接口受全局饱和寄存器影响，。特殊值：0→0；(2049,2050)→2050；(-2049,-2050)→-2050；(4097,4096)→4096；(4098,4100)→4100；(32776,32768)→32768；(32784,32800)→32800；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ll2half_rd](_ll2half_rd.md)（`related`）：RD 向负无穷取整，是 RNA 最近值舍入的定向替代。
- [__ll2half_ru](_ll2half_ru.md)（`related`）：RNA 采用最近且中点远离零，与 RU 的始终向正方向不同；两者不能因正数样例相同而混用。
- [__ll2half_rn](_ll2half_rn.md)（`same_topic`）：《__ll2half_rn》处理“遵循CAST_RINT模式，将int64类型数据转换为half类型数据，返回转换后的值。”。《__ll2half_rna》明确“遵循CAST_ROUND模式，将int64类型数据转换为half类型数据，返回转换后的值。”，可直接用于核对int64 到 half 转换的四种舍入方向选择合同。
- [__ll2half_rz](_ll2half_rz.md)（`same_topic`）：__ll2half_rz 与《__ll2half_rna》的实质衔接是：long long 到 half 的 RZ 转换需对照舍入方向、unsigned/float 和宽度 Cast 故障。
- [__ull2half_rna](_ull2half_rna.md)（`same_topic`）：__ull2half_rna 与《__ll2half_rna》的实质衔接是：uint64→half RNA 与其他舍入、有符号、bfloat16/float 目标变体共享大整数输入；UINT64 量化卡提供实际位宽约束。
<!-- cannbot:related:end -->
