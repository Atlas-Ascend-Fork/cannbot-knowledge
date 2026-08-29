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

- [__ll2half_rn](_ll2half_rn.md)（`same_topic`）：功能：遵循CAST_FLOOR模式，将int64类型数据转换为half类型数据，返回转换后的值。；功能：遵循CAST_RINT模式，将int64类型数据转换为half类型数据，返回转换后的值。。两接口转换相同 int64 输入到 half，核心差异是向下取整与就近取整模式，联合阅读可选择正确舍入契约。
<!-- cannbot:related:end -->
