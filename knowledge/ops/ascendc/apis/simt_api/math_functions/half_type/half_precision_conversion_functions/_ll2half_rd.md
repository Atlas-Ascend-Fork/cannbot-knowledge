---
type: API
title: __ll2half_rd
description: 遵循CAST_FLOOR模式，将int64类型数据转换为half类型数据，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half_precision_conversion_functions/__ll2half_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __ll2half_rd

功能：遵循CAST_FLOOR模式，将int64类型数据转换为half类型数据，返回转换后的值。

函数原型：half __ll2half_rd(const long long int x)

参数：x（输入）源操作数。

返回值：输入遵循CAST_FLOOR模式转换成的half类型数据。本接口受全局饱和寄存器影响，。特殊值：(9223372036854775807（long long最大值）,inf)→ASCRT_MAX_NORMAL_FP16；(-9223372036854775808（long long最小值）,-inf)→-ASCRT_MAX_NORMAL_FP16；ASCRT_MAX_NORMAL_FP16→ASCRT_MAX_NORMAL_FP16；-ASCRT_MAX_NORMAL_FP16→-ASCRT_MAX_NORMAL_FP16；(2049,2048)→2048；(2051,2052)→2052。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__ll2half_rna](_ll2half_rna.md)（`related`）：RD 向负无穷取整，是 RNA 最近值舍入的定向替代。
- [__ll2half_ru](_ll2half_ru.md)（`related`）：与 RU 相同 int64→half，但 RD 向负无穷取整；正负边界结果方向相反。
- [__ll2half_rn](_ll2half_rn.md)（`same_topic`）：《__ll2half_rn》处理“遵循CAST_RINT模式，将int64类型数据转换为half类型数据，返回转换后的值。”。《__ll2half_rd》明确“遵循CAST_FLOOR模式，将int64类型数据转换为half类型数据，返回转换后的值。”，可直接用于核对int64 到 half 转换的四种舍入方向选择合同。
- [__ll2half_rz](_ll2half_rz.md)（`same_topic`）：__ll2half_rz 与《__ll2half_rd》的实质衔接是：long long 到 half 的 RZ 转换需对照舍入方向、unsigned/float 和宽度 Cast 故障。
- [__ull2half_rd](_ull2half_rd.md)（`same_topic`）：__ull2half_rd 与《__ll2half_rd》的实质衔接是：这些接口共享 uint64→half 或相邻 signed/uint32 输入，RD/RZ/RN/RNA/RU 用于核对大整数窄化的舍入与符号边界。
<!-- cannbot:related:end -->
