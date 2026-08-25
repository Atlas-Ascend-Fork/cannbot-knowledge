---
type: API
title: H2Log
description: 获取以e为底，输入数据各元素的对数。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_math_functions/h2log.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# H2Log

功能：获取以e为底，输入数据各元素的对数。

函数原型：half2 h2log(half2 x)

参数：x（输入）源操作数。

返回值：以e为底的输入数据各元素的对数。本接口受全局饱和寄存器影响，。特殊值：±0→-ASCRT_MAX_NORMAL_FP16；nan→0；-inf→0；inf→ASCRT_MAX_NORMAL_FP16。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [H2Log](../../bfloat16_type/bfloat16x2_math_functions/h2log.md)（`same_topic`）：H2Log：H2Log、H2Log2、H2Log10分别计算e/2/10底对数，bfloat16x2同名接口提供类型变体；这些关系直接防止底数或数据类型选错。 目标卡《H2Log》补充：获取以e为底，输入数据各元素的对数。
- [H2Log10](h2log10.md)（`same_topic`）：H2Log：H2Log、H2Log2、H2Log10分别计算e/2/10底对数，bfloat16x2同名接口提供类型变体；这些关系直接防止底数或数据类型选错。 目标卡《H2Log10》补充：获取以10为底，输入数据各元素的对数。
- [H2Log2](h2log2.md)（`same_topic`）：H2Log：H2Log、H2Log2、H2Log10分别计算e/2/10底对数，bfloat16x2同名接口提供类型变体；这些关系直接防止底数或数据类型选错。 目标卡《H2Log2》补充：获取以2为底，输入数据各元素的对数。
<!-- cannbot:related:end -->
